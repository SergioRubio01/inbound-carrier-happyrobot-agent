/**
 * @file: sound.ts
 * @description: Sound utility functions for audio feedback
 */

// Simple sound utility for POC
// In a real app, you might use Web Audio API or a sound library

let audioContext: AudioContext | null = null;

// Initialize audio context
function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') {
    return null; // Server-side rendering
  }

  if (!audioContext) {
    try {
      audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (error) {
      console.warn('Audio context not supported:', error);
      return null;
    }
  }

  return audioContext;
}

// Play a simple error beep sound
export function playErrorSound(): void {
  const context = getAudioContext();
  if (!context) return;

  try {
    // Create oscillator for a simple beep
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    // Configure error sound (low frequency, brief)
    oscillator.frequency.setValueAtTime(300, context.currentTime);
    oscillator.type = 'sine';

    // Configure volume envelope
    gainNode.gain.setValueAtTime(0, context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.1, context.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.2);

    // Play the sound
    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.2);
  } catch (error) {
    console.warn('Failed to play error sound:', error);
  }
}

// Play a success sound
export function playSuccessSound(): void {
  const context = getAudioContext();
  if (!context) return;

  try {
    // Create oscillator for a simple chime
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    // Configure success sound (higher frequency, pleasant)
    oscillator.frequency.setValueAtTime(600, context.currentTime);
    oscillator.frequency.linearRampToValueAtTime(800, context.currentTime + 0.1);
    oscillator.type = 'sine';

    // Configure volume envelope
    gainNode.gain.setValueAtTime(0, context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.1, context.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.3);

    // Play the sound
    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.3);
  } catch (error) {
    console.warn('Failed to play success sound:', error);
  }
}

// Play a notification sound
export function playNotificationSound(): void {
  const context = getAudioContext();
  if (!context) return;

  try {
    // Create oscillator for a gentle notification
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    // Configure notification sound (mid frequency, brief)
    oscillator.frequency.setValueAtTime(400, context.currentTime);
    oscillator.type = 'sine';

    // Configure volume envelope
    gainNode.gain.setValueAtTime(0, context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.08, context.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.15);

    // Play the sound
    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.15);
  } catch (error) {
    console.warn('Failed to play notification sound:', error);
  }
}
