import { MongoClient } from 'mongodb';
import { OpenAI } from 'openai';
import { generateVector } from './processor';
import { runQuery, Patient } from '@/utils/mongoquery';

const openai = new OpenAI({apiKey: process.env.OPENAI_API_KEY});

export async function searchDocuments(query: string): Promise<string> {
  const queryVector = generateVector(query);
  const k = 1;

  const pipeline = [
    {
      $vectorSearch: {
        index: 'vector_index',
        path: 'vector',
        queryVector: queryVector,
        numCandidates: 5,
        limit: 1,
      },
    },
  ];

  const results = await runQuery<Patient>('GPTFUN', 'patient', pipeline);

  let userMessageWithContext = '\n# User query:\n' + query;

  if (results.length > 0) {
    const result = results[0].summary;
    userMessageWithContext +=
      '# Context for the user query below, do not mention the query in your response:\n' +
      result +
      userMessageWithContext;
  }

  const response = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo',
    messages: [
      {
        role: 'system',
        content:
          'You are an expert physician that is answering questions for the patient.\n' +
          'If the user asks for information that is not consistent with the context explain potential misunderstandings' +
          'Talk to the patient in second person. Say you as if you were talking to the user.',
      },
      { role: 'user', content: query },
      { role: 'user', content: userMessageWithContext },
    ],
  });

  return response.choices[0].message.content || 'Error Fetching Data';
}