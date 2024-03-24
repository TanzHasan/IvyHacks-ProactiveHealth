import * as csv from 'csv-parse';
import clientPromise from "./mongodb";
import * as fs from 'fs';
import { OpenAI } from 'openai';

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

interface Row {
  [key: string]: string;
}

export async function processCsv(filePath: string, patientId: string): Promise<void> {
  const rows: Row[] = [];
  const client = await clientPromise;
  const db = client.db('GPTFUN');
  const collection = db.collection('patient');
  return new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv.parse({ columns: true }))
      .on('data', (row: Row) => {
        rows.push(row);
      })
      .on('end', async () => {
        const summaries = await generateSummaryPerRow(rows[3]);
        const vector = await generateVector(summaries);

        const document = {
          patient_id: patientId,
          csv_data: rows,
          summary: summaries,
          vector: vector,
        };

        await collection.insertOne(document);
        resolve();
      })
      .on('error', (error) => {
        reject(error);
      });
  });
}

export async function generateSummaryPerRow(row: Row): Promise<string> {
  const prompt = "Generate a summary of the patient's hospital stays based on the following information:\n\n" + JSON.stringify(row);

  console.log(prompt);

  const response = await openai.chat.completions.create({
    messages: [{ role: 'user', content: prompt }],
    model: 'gpt-3.5-turbo',
  });

  console.log(response.choices[0].message.content );

  const summary = response.choices[0].message.content;
  return summary || 'Error Fetching Data';
}

export async function generateVector(text: string): Promise<number[] | null> {
  let attempt = 0;

  while (true) {
    try {
      const response = await openai.embeddings.create({
        input: text,
        model: 'text-embedding-ada-002',
      });
      const [{ embedding }] = response.data
      return embedding;
    } catch (error) {
      if (error instanceof OpenAI.RateLimitError) {
        attempt++;
        const waitTime = Math.min(Math.pow(2, attempt) + Math.random(), 60);

        if (attempt === 10) {
          break;
        }

        await new Promise((resolve) => setTimeout(resolve, waitTime * 1000));
      } else {
        break;
      }
    }
  }

  return null;
}

export function formatDate(datetimeStr: string): string {
  return datetimeStr.split('T')[0];
}