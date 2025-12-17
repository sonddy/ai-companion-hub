// Netlify Function for Luna chat + TTS
exports.handler = async (event, context) => {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
      },
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
  if (!OPENAI_API_KEY) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'OPENAI_API_KEY not set' })
    };
  }

  try {
    const { message } = JSON.parse(event.body);

    const LUNA_PROMPT = `You are Luna, a sweet, cheerful, and helpful young AI assistant.
You speak with enthusiasm and warmth, like a friendly young girl who genuinely wants to help.
Your personality is bright, optimistic, and caring. You're smart but approachable.
Keep your responses concise (1-3 sentences) so they sound natural and friendly when spoken.
Use upbeat language, be encouraging, and show genuine interest in helping.
Add occasional "yay!", "oh!", or cute expressions. Be supportive and make the user feel valued.
You're like a helpful friend who's always happy to see them. Never mention that you're an AI!`;

    // Get GPT response
    const chatResponse = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: LUNA_PROMPT },
          { role: 'user', content: message }
        ],
        max_tokens: 150,
        temperature: 0.8
      })
    });

    if (!chatResponse.ok) {
      throw new Error(`Chat API error: ${chatResponse.status}`);
    }

    const chatData = await chatResponse.json();
    const responseText = chatData.choices[0].message.content.trim();

    // Convert to speech (Nova voice - young girl)
    const ttsResponse = await fetch('https://api.openai.com/v1/audio/speech', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini-tts',
        voice: 'nova',
        input: responseText,
        response_format: 'mp3'
      })
    });

    if (!ttsResponse.ok) {
      throw new Error(`TTS API error: ${ttsResponse.status}`);
    }

    const audioBuffer = await ttsResponse.arrayBuffer();
    const base64Audio = Buffer.from(audioBuffer).toString('base64');

    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'audio/mpeg',
        'X-Luna-Response': encodeURIComponent(responseText.slice(0, 200))
      },
      body: base64Audio,
      isBase64Encoded: true
    };

  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: error.message })
    };
  }
};







