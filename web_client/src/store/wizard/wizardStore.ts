/**
 * @file web_client/src/store/wizard/wizardStore.ts
 * @description Zustand store for managing the state of the Project Wizard.
 * @author HappyRobot Team
 * @created 2025-05-07
 * @lastModified 2025-05-07
 *
 * Modification History:
 * - 2025-05-07: Initial creation of the wizard store.
 *
 * Dependencies:
 * - zustand
 * - ../../components/wizard/EventStreamDisplay (WizardEventViewData)
 * - ../../components/wizard/TemplateSelectionModal (TemplateKey) - if type used here
 * - ../../lib/wizardUtils (formatRawEventToViewData)
 */

import { create } from 'zustand';
import { WizardEventViewData } from '@/components/wizard/EventStreamDisplay';
import { TemplateKey } from '@/components/wizard/TemplateSelectionModal';
import { formatRawEventToViewData } from '@/lib/wizardUtils'; // Assuming this path

export type WizardStep = 'templateSelection' | 'promptInput' | 'processing' | 'completed' | 'error';

interface WizardState {
  wizardStep: WizardStep;
  selectedTemplateKey: TemplateKey | null;
  promptText: string; // Store the prompt text
  executionId: string | null;
  projectId: string | null; // Add projectId
  events: WizardEventViewData[];
  isLoadingApi: boolean; // For API calls like starting a project
  isSocketConnected: boolean;
  error: string | null; // For storing error messages

  setWizardStep: (step: WizardStep) => void;
  selectTemplate: (templateKey: TemplateKey) => void;
  setPromptText: (prompt: string) => void;
  startProjectGeneration: (apiCall: () => Promise<{ success: boolean, execution_id?: string, project_id?: string, error?: string }>) => Promise<void>;
  addRawEvent: (rawEvent: any) => void;
  setIsSocketConnected: (isConnected: boolean) => void;
  setError: (errorMessage: string | null) => void;
  resetWizard: () => void;
  setProjectDetails: (details: { projectId: string | null; executionId?: string | null }) => void; // Add setProjectDetails action
}

const initialState = {
  wizardStep: 'templateSelection' as WizardStep,
  selectedTemplateKey: null as TemplateKey | null,
  promptText: '',
  executionId: null as string | null,
  projectId: null as string | null, // Initialize projectId
  events: [] as WizardEventViewData[],
  isLoadingApi: false,
  isSocketConnected: false,
  error: null as string | null,
};

export const useWizardStore = create<WizardState>((set, get) => ({
  ...initialState,

  setWizardStep: (step) => set({ wizardStep: step, error: null }), // Clear error on step change

  selectTemplate: (templateKey) => set({
    selectedTemplateKey: templateKey,
    wizardStep: 'promptInput', // Automatically move to next step
    error: null,
    promptText: '', // Clear previous prompt
  }),

  setPromptText: (prompt) => set({ promptText: prompt }),

  startProjectGeneration: async (apiCall) => {
    set({ isLoadingApi: true, error: null, events: [], executionId: null, projectId: null });
    try {
      const response = await apiCall();
      if (response.success && response.execution_id) {
        set({
          executionId: response.execution_id,
          ...(response.project_id && { projectId: response.project_id }), // Also set projectId here if returned by API directly
          wizardStep: 'processing',
          isLoadingApi: false
        });
      } else {
        set({ error: response.error || 'API call failed.', wizardStep: 'error', isLoadingApi: false });
      }
    } catch (err: any) {
      set({ error: err.message || 'An unexpected error occurred.', wizardStep: 'error', isLoadingApi: false });
    }
  },

  addRawEvent: (rawEvent) => {
    const formattedEvent = formatRawEventToViewData(rawEvent);
    set((state) => ({ events: [...state.events, formattedEvent] }));
    // Optionally, update wizardStep if a "completed" or "error" event is received from WebSocket
    // For example:
    // if (formattedEvent.type === 'project.generation.completed') {
    //   set({ wizardStep: 'completed', isLoadingApi: false });
    // } else if (formattedEvent.type === 'project.generation.failed') {
    //   set({ wizardStep: 'error', error: formattedEvent.displayText, isLoadingApi: false });
    // }
  },

  setIsSocketConnected: (isConnected) => set({ isSocketConnected: isConnected }),

  setError: (errorMessage) => set({ error: errorMessage, wizardStep: 'error' }),

  resetWizard: () => set({ ...initialState }),

  setProjectDetails: (details) => set({
    projectId: details.projectId,
    ...(details.executionId && { executionId: details.executionId }) // Optionally update executionId if provided
  }),
}));
