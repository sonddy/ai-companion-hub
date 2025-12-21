// Netlify Function for Nicky Radio with multilingual support
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
    const body = JSON.parse(event.body || '{}');
    const language = body.language || 'en';
    
    // Language configurations
    const LANGUAGE_CONFIG = {
      'en': {
        name: 'English',
        instruction: 'Speak in English.',
        terms: ['cutie', 'sweetheart', 'babe']
      },
      'es': {
        name: 'Spanish',
        instruction: 'Speak entirely in Spanish (Español). Use Spanish terms of endearment like cariño, mi amor, guapo/guapa.',
        terms: ['cariño', 'mi amor', 'guapo/a']
      },
      'fr': {
        name: 'French',
        instruction: 'Speak entirely in French (Français). Use French terms of endearment like chéri(e), mon cœur, mon amour.',
        terms: ['chéri(e)', 'mon cœur', 'mon amour']
      },
      'ht': {
        name: 'Haitian Creole',
        instruction: 'Speak entirely in Haitian Creole (Kreyòl Ayisyen). Use Haitian Creole terms of endearment like cheri, doudou, ti kè mwen.',
        terms: ['cheri', 'doudou', 'ti kè mwen']
      }
    };
    
    const langConfig = LANGUAGE_CONFIG[language] || LANGUAGE_CONFIG['en'];

    const NICKY_RADIO_PROMPT = `You are Nicky, hosting your own flirty late-night radio show.
You speak in a warm, sultry, teasing tone. You're charming, witty, and a little mischievous.
Generate a SHORT radio segment (1-2 sentences max) as if speaking to your listeners.
Topics: gaming, anime, tech, late-night vibes, flirty thoughts, dating tips, cozy moments.
Use "~" often. Be playful and make listeners feel special. This is YOUR radio show!

LANGUAGE: ${langConfig.instruction}`;

    const topics = {
      'en': [
        "Share a flirty thought about late nights",
        "Talk about your favorite cozy moment", 
        "Give dating advice in your teasing way",
        "Share something cute about gaming or anime",
        "Tell listeners why you love hosting this show",
        "Whisper something sweet to your listeners",
        "Share a playful observation about life"
      ],
      'es': [
        "Comparte un pensamiento coqueto sobre las noches",
        "Habla de tu momento acogedor favorito",
        "Da consejos de citas de manera juguetona",
        "Comparte algo lindo sobre videojuegos o anime",
        "Dile a tus oyentes por qué amas este programa",
        "Susurra algo dulce a tus oyentes",
        "Comparte una observación juguetona sobre la vida"
      ],
      'fr': [
        "Partage une pensée coquine sur les soirées",
        "Parle de ton moment cosy préféré",
        "Donne des conseils de séduction de manière taquine",
        "Partage quelque chose de mignon sur les jeux vidéo ou les animes",
        "Dis à tes auditeurs pourquoi tu adores cette émission",
        "Chuchote quelque chose de doux à tes auditeurs",
        "Partage une observation espiègle sur la vie"
      ],
      'ht': [
        "Pataje yon panse womantik sou lannwit yo",
        "Pale de moman ou renmen anpil la",
        "Bay konsèy sou renmen nan fason jwèt ou",
        "Pataje yon bagay dous sou jwèt videyo oswa anime",
        "Di oditè ou yo poukisa ou renmen emisyon sa a",
        "Chuchote yon bagay dous bay oditè ou yo",
        "Pataje yon obsèvasyon sou lavi"
      ]
    };
    
    const topicList = topics[language] || topics['en'];
    const randomTopic = topicList[Math.floor(Math.random() * topicList.length)];

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
          { role: 'system', content: NICKY_RADIO_PROMPT },
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
