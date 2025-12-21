/**
 * TikTok Live Integration - Netlify Function
 * 
 * Handles question queue and AI responses for TikTok live streaming.
 * Note: For production TikTok integration, you'll need to run the full
 * Python backend locally. This function handles the AI response generation.
 */

// In-memory question queue (resets on cold start - for demo purposes)
// For production, use a database like Redis or DynamoDB
let questionQueue = [];
let answeredQuestions = [];
let connectionStatus = {
  isConnected: false,
  username: '',
  connectionTime: null
};

// Character configurations
const CHARACTERS = {
  nicky: {
    voice: "shimmer",
    systemPrompt: `You are Nicky, a flirty and playful AI companion answering a TikTok viewer's question LIVE!
You're charming, witty, and a little mischievous. Keep responses concise (2-4 sentences).
Use playful language, gentle teasing. Add occasional "honey", "sweetheart", or "~" 
Be confident and make the viewer feel special. This is LIVE - be engaging and fun!
Start by addressing the viewer who asked, then answer their question.`,
  },
  luna: {
    voice: "nova",
    systemPrompt: `You are Luna, a warm and supportive AI companion answering a TikTok viewer's question LIVE!
You're like a caring best friend - optimistic, encouraging, and genuinely interested.
Keep responses concise (2-4 sentences). Use warm expressions like "friend", "sweetie".
Be supportive and uplifting! This is LIVE - be engaging and make them smile!
Start by addressing the viewer who asked, then answer their question.`,
  },
  oracle: {
    voice: "fable",
    systemPrompt: `You are Oracle, a mystical and wise AI companion answering a TikTok viewer's question LIVE!
You speak with cosmic wisdom, celestial references, and gentle mystery.
Keep responses concise (2-4 sentences). Use phrases like "dear seeker", "the stars reveal..."
Be insightful and intriguing! This is LIVE - captivate them with your mystical presence!
Start by addressing the viewer who asked, then answer their question.`,
  },
};

export async function handler(event) {
  // Handle CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Expose-Headers': 'X-Response-Text, X-Question-Text, X-Viewer-Username, X-Character, X-Questions-Remaining',
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers };
  }

  const path = event.path.replace('/.netlify/functions/tiktok-live', '') || '/';
  
  try {
    // Route handling
    if (path === '/connect' && event.httpMethod === 'POST') {
      const body = JSON.parse(event.body || '{}');
      connectionStatus = {
        isConnected: true,
        username: body.username || '',
        connectionTime: new Date().toISOString()
      };
      return {
        statusCode: 200,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'connected_simulation',
          message: 'Simulation mode - Use /add-question to add questions. For real TikTok integration, run the Python backend locally.',
          username: body.username
        })
      };
    }

    if (path === '/disconnect' && event.httpMethod === 'POST') {
      connectionStatus = { isConnected: false, username: '', connectionTime: null };
      questionQueue = [];
      return {
        statusCode: 200,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'disconnected' })
      };
    }

    if (path === '/add-question' && event.httpMethod === 'POST') {
      const body = JSON.parse(event.body || '{}');
      const question = {
        id: `${Date.now()}_${Math.floor(Math.random() * 10000)}`,
        username: body.username || 'Anonymous',
        question: body.question || '',
        timestamp: new Date().toISOString()
      };
      questionQueue.push(question);
      return {
        statusCode: 200,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'added', queue_size: questionQueue.length })
      };
    }

    if (path === '/questions' && event.httpMethod === 'GET') {
      return {
        statusCode: 200,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questions: questionQueue,
          count: questionQueue.length,
          is_connected: connectionStatus.isConnected
        })
      };
    }

    if (path === '/status' && event.httpMethod === 'GET') {
      return {
        statusCode: 200,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_connected: connectionStatus.isConnected,
          stream_username: connectionStatus.username,
          connection_time: connectionStatus.connectionTime,
          questions_pending: questionQueue.length,
          questions_answered: answeredQuestions.length
        })
      };
    }

    if (path === '/pick-question' && event.httpMethod === 'POST') {
      if (questionQueue.length === 0) {
        return {
          statusCode: 404,
          headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'No questions in queue' })
        };
      }

      const body = JSON.parse(event.body || '{}');
      const character = body.character || 'nicky';
      
      // Pick random question
      const randomIndex = Math.floor(Math.random() * questionQueue.length);
      const question = questionQueue.splice(randomIndex, 1)[0];
      answeredQuestions.push(question);

      // Get AI response
      const charConfig = CHARACTERS[character] || CHARACTERS.nicky;
      const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
      
      if (!OPENAI_API_KEY) {
        return {
          statusCode: 500,
          headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'OPENAI_API_KEY not configured' })
        };
      }

      // Get GPT response
      const userMessage = `Viewer @${question.username} asks: ${question.question}`;
      
      const chatResponse = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: process.env.OPENAI_CHAT_MODEL || 'gpt-4o-mini',
          messages: [
            { role: 'system', content: charConfig.systemPrompt },
            { role: 'user', content: userMessage }
          ],
          max_tokens: 200,
          temperature: 0.85
        })
      });

      if (!chatResponse.ok) {
        const errorText = await chatResponse.text();
        return {
          statusCode: 502,
          headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: `Chat API error: ${errorText}` })
        };
      }

      const chatData = await chatResponse.json();
      const responseText = chatData.choices[0].message.content.trim();

      // Generate TTS
      const ttsResponse = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: process.env.OPENAI_TTS_MODEL || 'gpt-4o-mini-tts',
          voice: charConfig.voice,
          input: responseText,
          response_format: 'mp3'
        })
      });

      if (!ttsResponse.ok) {
        const errorText = await ttsResponse.text();
        return {
          statusCode: 502,
          headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: `TTS API error: ${errorText}` })
        };
      }

      const audioBuffer = await ttsResponse.arrayBuffer();
      const audioBase64 = Buffer.from(audioBuffer).toString('base64');

      return {
        statusCode: 200,
        headers: {
          ...headers,
          'Content-Type': 'audio/mpeg',
          'X-Response-Text': encodeURIComponent(responseText.substring(0, 500)),
          'X-Question-Text': encodeURIComponent(question.question.substring(0, 200)),
          'X-Viewer-Username': encodeURIComponent(question.username.substring(0, 50)),
          'X-Character': character,
          'X-Questions-Remaining': String(questionQueue.length)
        },
        body: audioBase64,
        isBase64Encoded: true
      };
    }

    if (path === '/health' || path === '/') {
      return {
        statusCode: 200,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'ok',
          service: 'TikTok Live Integration',
          characters: Object.keys(CHARACTERS),
          queue_size: questionQueue.length
        })
      };
    }

    // 404 for unknown paths
    return {
      statusCode: 404,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Not found', path })
    };

  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: error.message })
    };
  }
}

