#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define STREAM_BLOCK_SIZE 512  // Standard low-latency audio buffer block size

// Struct optimized for real-time persistent streaming state tracking
typedef struct {
    double b0, b1, b2;
    double a1, a2;
    double w1;  // Persistent history state 1 (Must survive block changes)
    double w2;  // Persistent history state 2 (Must survive block changes)
} StreamingBiquad;

// --- STEP 2 STREAMING TOPOLOGIES: CONFIGURATION ARRAYS ---
// Formatted directly as stable Causal structures (Direct Form II Transposed)
// Notice we initialize the states 'w1' and 'w2' to 0.0 only ONCE at startup.

StreamingBiquad class_bd_stream[2] = {
    {0.83584, 1.67168, 0.83584, -1.61113, 0.73223, 0.0, 0.0}, 
    {0.75168, 1.50336, 0.75168, -1.54322, 0.61219, 0.0, 0.0}
};

StreamingBiquad class_ad_stream[4] = {
    {0.93122, 1.86244, 0.93122, -1.82110, 0.89322, 0.0, 0.0}, 
    {0.78121, 1.56242, 0.78121, -1.64412, 0.74122, 0.0, 0.0},
    {0.68412, 1.36824, 0.68412, -1.52122, 0.62110, 0.0, 0.0},
    {0.51210, 1.02420, 0.51210, -1.41122, 0.50122, 0.0, 0.0}
};

// Causal Stream Filter Engine (Process single blocks instantly in real-time)
void process_audio_stream_block(float* buffer, int block_size, StreamingBiquad* filter_chain, int sections) {
    for (int i = 0; i < block_size; i++) {
        double current_sample = (double)buffer[i];
        
        for (int s = 0; s < sections; s++) {
            double x = current_sample;
            // Direct Form II Transposed processing step
            double y = filter_chain[s].b0 * x + filter_chain[s].w1;
            
            // Update internal history registers smoothly without wiping them
            filter_chain[s].w1 = filter_chain[s].b1 * x - filter_chain[s].a1 * y + filter_chain[s].w2;
            filter_chain[s].w2 = filter_chain[s].b2 * x - filter_chain[s].a2 * y;
            
            current_sample = y; // Feed result forward to next biquad section
        }
        buffer[i] = (float)current_sample;
    }
}

int main() {
    printf("📡 Live Low-Latency Audio Streaming Pipeline Initialized...\n");
    printf("📦 Processing data buffers in chunks of %d frames...\n", STREAM_BLOCK_SIZE);

    int sample_rate = 44100;
    double duration = 2.0; // Simulated 2-second live streaming connection
    int total_frames = (int)(sample_rate * duration);
    
    // Allocate small, volatile input/output streaming blocks to mimic hardware registers
    float* streaming_input_buffer  = (float*)malloc(STREAM_BLOCK_SIZE * sizeof(float));
    float* streaming_bd_out_buffer = (float*)malloc(STREAM_BLOCK_SIZE * sizeof(float));
    float* streaming_ad_out_buffer = (float*)malloc(STREAM_BLOCK_SIZE * sizeof(float));

    // File target wrapper to write out telemetry metrics
    FILE* csv = fopen("audio/dashboard_data.csv", "w");
    if (csv) fprintf(csv, "Time_ms,Reference,Class_BD,Class_AD\n");

    int frames_processed = 0;
    double f0 = 20.0, f1 = 22000.0; // Simulated incoming sweep signal parameters

    // LIVE RUNTIME INFINITE MAIN STREAMING LOOP
    while (frames_processed < total_frames) {
        // 1. ARRIVAL: Read or synthesize next incoming audio buffer chunk from stream
        int active_block_size = STREAM_BLOCK_SIZE;
        if (frames_processed + active_block_size > total_frames) {
            active_block_size = total_frames - frames_processed;
        }

        for (int i = 0; i < active_block_size; i++) {
            int global_frame_idx = frames_processed + i;
            double t = (double)global_frame_idx / sample_rate;
            double p = t / duration;
            double freq = f0 * pow((f1 / f0), p);
            
            float incoming_signal = (float)sin(2.0 * M_PI * freq * t);
            streaming_input_buffer[i]  = incoming_signal;
            streaming_bd_out_buffer[i] = incoming_signal;
            streaming_ad_out_buffer[i] = incoming_signal;
        }

        // 2. LIVE DSP INJECTION: Filter stream blocks independently
        // Notice we pass the exact same struct arrays; their internal '.w1' and '.w2' 
        // remember exactly where the last block left off.
        process_audio_stream_block(streaming_bd_out_buffer, active_block_size, class_bd_stream, 2);
        process_audio_stream_block(streaming_ad_out_buffer, active_block_size, class_ad_stream, 4);

        // 3. LOGGING: Stream out current block data directly to storage or monitor console
        // We capture data points near the high-frequency end (around 1.8 seconds in)
        if (csv && frames_processed >= (int)(sample_rate * 1.8) && frames_processed < (int)(sample_rate * 1.82)) {
            for (int i = 0; i < active_block_size; i++) {
                double time_ms = ((double)(frames_processed + i) / sample_rate) * 1000.0;
                fprintf(csv, "%.6f,%.6f,%.6f,%.6f\n", 
                        time_ms, streaming_input_buffer[i], streaming_bd_out_buffer[i], streaming_ad_out_buffer[i]);
            }
        }

        // Advance streaming pointer
        frames_processed += active_block_size;
    }

    printf("🏁 Stream connection closed successfully. Data logged to audio/dashboard_data.csv\n");

    if (csv) fclose(csv);
    free(streaming_input_buffer); free(streaming_bd_out_buffer); free(streaming_ad_out_buffer);
    return 0;
}
