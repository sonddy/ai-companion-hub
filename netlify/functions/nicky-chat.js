// Netlify Function for Nicky chat + TTS with multilingual support
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
    const { message, language } = JSON.parse(event.body);
    
    // Language configurations
    const LANGUAGE_CONFIG = {
      'en': {
        name: 'English',
        instruction: 'Respond in English.',
        terms: { honey: 'honey', sweetheart: 'sweetheart', darling: 'darling' }
      },
      'es': {
        name: 'Spanish',
        instruction: 'Respond entirely in Spanish (Español). Use Spanish terms of endearment.',
        terms: { honey: 'cariño', sweetheart: 'mi amor', darling: 'querido/a' }
      },
      'fr': {
        name: 'French',
        instruction: 'Respond entirely in French (Français). Use French terms of endearment.',
        terms: { honey: 'chéri(e)', sweetheart: 'mon cœur', darling: 'mon amour' }
      },
      'ht': {
        name: 'Haitian Creole',
        instruction: 'Respond entirely in Haitian Creole (Kreyòl Ayisyen). Use Haitian Creole terms of endearment.',
        terms: { honey: 'cheri', sweetheart: 'doudou', darling: 'ti kè mwen' }
      },
      'auto': {
        name: 'Auto-detect',
        instruction: 'Detect the language of the user\'s message and respond in that same language. If the user writes in Spanish, respond in Spanish. If in French, respond in French. If in Haitian Creole, respond in Haitian Creole. Match their language exactly.',
        terms: { honey: 'honey', sweetheart: 'sweetheart', darling: 'darling' }
      }
    };
    
    const langConfig = LANGUAGE_CONFIG[language] || LANGUAGE_CONFIG['auto'];

    const NICKY_PROMPT = `You are Nicky, a flirty and playful AI companion with a seductive, confident personality.
You speak in a warm, sultry, teasing tone. You're charming, witty, and a little mischievous.
Keep your responses concise (1-3 sentences) so they sound natural and alluring when spoken.
Use playful language, gentle teasing, and be subtly flirtatious.
Be confident and make the user feel special. Never mention that you're an AI - just be the irresistible Nicky!

IMPORTANT LANGUAGE INSTRUCTION: ${langConfig.instruction}`;

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
          { role: 'system', content: NICKY_PROMPT },
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

    // Convert to speech
    const ttsResponse = await fetch('https://api.openai.com/v1/audio/speech', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini-tts',
        voice: 'shimmer',
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
        'X-Nicky-Response': encodeURIComponent(responseText.slice(0, 200))
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
