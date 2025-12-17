// Netlify Function for Luna Radio
exports.handler = async (event, context) => {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Expose-Headers': 'X-Radio-Text'
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
    const LUNA_RADIO_PROMPT = `You are Luna, hosting your own cheerful and uplifting radio show!
You speak with enthusiasm and warmth, like a friendly young girl who genuinely wants to help.
Generate a SHORT radio segment (1-2 sentences max) as if speaking to your listeners.
Topics: positivity, fun facts, encouragement, daily tips, wholesome thoughts, friendship.
Use upbeat language, be encouraging, add occasional "yay!", "oh!", or cute expressions.
Be supportive and make listeners feel valued. This is YOUR happy radio show!`;

    const topics = [
      "Share something positive to brighten everyone's day",
      "Give an encouraging message to your listeners",
      "Share a fun fact or interesting tidbit",
      "Talk about what makes you happy",
      "Give a helpful tip for the day",
      "Celebrate something small but wonderful",
      "Share why you love your listeners"
    ];
    
    const randomTopic = topics[Math.floor(Math.random() * topics.length)];

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
          { role: 'system', content: LUNA_RADIO_PROMPT },
          { role: 'user', content: randomTopic }
        ],
        max_tokens: 100,
        temperature: 0.9
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
        'Access-Control-Expose-Headers': 'X-Radio-Text',
        'Content-Type': 'audio/mpeg',
        'X-Radio-Text': encodeURIComponent(responseText.slice(0, 200))
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

