import { api } from './api'

/** Submit an answer index and receive the scored attempt result. */
export const submitQuizAttempt = (conceptId: string, answerIndex: number) =>
  api<{ attempt_id: string; correct: boolean; score: number }>(`/quizzes/${conceptId}/attempts`, { method: 'POST', body: JSON.stringify({ answer_index: answerIndex }) })
