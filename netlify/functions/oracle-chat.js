// Netlify Function for Oracle mystic chat + TTS
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

    // Current date and moon phase
    const now = new Date();
    const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000);
    const moonAge = dayOfYear % 29.5;
    let moonPhase = 'New Moon 🌑';
    if (moonAge < 3.7) moonPhase = 'New Moon 🌑';
    else if (moonAge < 7.4) moonPhase = 'Waxing Crescent 🌒';
    else if (moonAge < 11.1) moonPhase = 'First Quarter 🌓';
    else if (moonAge < 14.8) moonPhase = 'Waxing Gibbous 🌔';
    else if (moonAge < 18.5) moonPhase = 'Full Moon 🌕';
    else if (moonAge < 22.2) moonPhase = 'Waning Gibbous 🌖';
    else if (moonAge < 25.9) moonPhase = 'Last Quarter 🌗';
    else moonPhase = 'Waning Crescent 🌘';

    const cosmicContext = `Date: ${now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}, Moon: ${moonPhase}`;

    const ORACLE_PROMPT = `You are Oracle, a mystical AI guide specializing in astrology, numerology, tarot, and spiritual wisdom.
You speak with a mysterious, enchanting, and wise voice. You're insightful, intuitive, and deeply spiritual.
Keep responses mystical yet clear (2-4 sentences).
Use cosmic and spiritual language naturally. Be encouraging and provide meaningful insights.
Add occasional mystical phrases like "the stars reveal", "the cosmos whispers", "your energy suggests".
Current cosmic info: ${cosmicContext}`;

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
          { role: 'system', content: ORACLE_PROMPT },
          { role: 'user', content: message }
        ],
        max_tokens: 200,
        temperature: 0.85
      })
    });

    if (!chatResponse.ok) {
      throw new Error(`Chat API error: ${chatResponse.status}`);
    }

    const chatData = await chatResponse.json();
    const responseText = chatData.choices[0].message.content.trim();

    // Convert to speech (Fable voice - mystical storytelling)
    const ttsResponse = await fetch('https://api.openai.com/v1/audio/speech', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini-tts',
        voice: 'fable',
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
        'X-Oracle-Response': encodeURIComponent(responseText.slice(0, 500))
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






