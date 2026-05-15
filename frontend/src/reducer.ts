import type { AppAction, AppState } from './types'

export const initialState: AppState = {
  phase: 'idle',
  inputMethod: null,
  parsedFile: null,
  validationData: null,
  companyName: '',
  selectedRetailer: 'All Retailers',
  activeSection: 'issues',
  error: null,
}

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_INPUT_METHOD':
      return {
        ...state,
        inputMethod: action.method,
        parsedFile: null,
        error: null,
      }
    case 'FILE_PARSED':
      return { ...state, parsedFile: action.payload }
    case 'SET_COLUMN':
      if (!state.parsedFile) return state
      return {
        ...state,
        parsedFile: {
          ...state.parsedFile,
          selectedGtinColumn: action.column,
          gtins: state.parsedFile.previewRows.map(
            (r) => r[action.column] ?? '',
          ).filter(Boolean),
        },
      }
    case 'VALIDATION_START':
      return { ...state, phase: 'loading', error: null }
    case 'VALIDATION_SUCCESS':
      return { ...state, phase: 'results', validationData: action.data }
    case 'VALIDATION_ERROR':
      return { ...state, phase: 'idle', error: action.error }
    case 'START_OVER':
      return { ...initialState }
    case 'SET_COMPANY_NAME':
      return { ...state, companyName: action.name }
    case 'SET_RETAILER':
      return { ...state, selectedRetailer: action.retailer }
    case 'SET_ACTIVE_SECTION':
      return { ...state, activeSection: action.section }
  }
}
