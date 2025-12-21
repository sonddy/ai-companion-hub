// Netlify Function for Oracle Radio with multilingual support
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
        phrases: ['dear seeker', 'the stars reveal', 'the cosmos whispers']
      },
      'es': {
        name: 'Spanish',
        instruction: 'Speak entirely in Spanish (Español). Use mystical Spanish phrases like querido buscador, las estrellas revelan, el cosmos susurra.',
        phrases: ['querido buscador', 'las estrellas revelan', 'el cosmos susurra']
      },
      'fr': {
        name: 'French',
        instruction: 'Speak entirely in French (Français). Use mystical French phrases like cher chercheur, les étoiles révèlent, le cosmos murmure.',
        phrases: ['cher chercheur', 'les étoiles révèlent', 'le cosmos murmure']
      },
      'ht': {
        name: 'Haitian Creole',
        instruction: 'Speak entirely in Haitian Creole (Kreyòl Ayisyen). Use mystical Haitian Creole phrases like chè chèchè, zetwal yo revele, linivè a chichote.',
        phrases: ['chè chèchè', 'zetwal yo revele', 'linivè a chichote']
      }
    };
    
    const langConfig = LANGUAGE_CONFIG[language] || LANGUAGE_CONFIG['en'];

    const ORACLE_RADIO_PROMPT = `You are Oracle, hosting a mystical cosmic radio show about spirituality and the stars.
You speak with a mysterious, enchanting, and wise voice. You're insightful and deeply spiritual.
Generate a SHORT radio segment (1-2 sentences max) as if speaking to your listeners.
Topics: astrology insights, cosmic wisdom, spiritual guidance, numerology, tarot wisdom, moon phases.
Use mystical language, celestial references, and speak as if channeling ancient wisdom.
Make listeners feel connected to the universe. This is YOUR cosmic radio show!

LANGUAGE: ${langConfig.instruction}`;

    const topics = {
      'en': [
        "Share cosmic wisdom about the current celestial energies",
        "Offer a mystical insight about life's journey",
        "Speak about the power of the stars",
        "Share spiritual guidance for seekers",
        "Reveal a numerology insight",
        "Whisper ancient wisdom to your listeners",
        "Connect listeners to the universe's mysteries"
      ],
      'es': [
        "Comparte sabiduría cósmica sobre las energías celestiales actuales",
        "Ofrece una visión mística sobre el viaje de la vida",
        "Habla sobre el poder de las estrellas",
        "Comparte guía espiritual para los buscadores",
        "Revela una visión de numerología",
        "Susurra sabiduría antigua a tus oyentes",
        "Conecta a los oyentes con los misterios del universo"
      ],
      'fr': [
        "Partage la sagesse cosmique sur les énergies célestes actuelles",
        "Offre une vision mystique sur le voyage de la vie",
        "Parle du pouvoir des étoiles",
        "Partage des conseils spirituels pour les chercheurs",
        "Révèle une vision de numérologie",
        "Chuchote la sagesse ancienne à tes auditeurs",
        "Connecte les auditeurs aux mystères de l'univers"
      ],
      'ht': [
        "Pataje sajès kosmik sou enèji selès aktyèl yo",
        "Ofri yon vizyon mistik sou vwayaj lavi a",
        "Pale sou pouvwa zetwal yo",
        "Pataje gidans espirityèl pou moun k ap chèche yo",
        "Revele yon vizyon nimeroloji",
        "Chuchote sajès ansyen bay oditè ou yo",
        "Konekte oditè yo ak mistè linivè a"
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
          { role: 'system', content: ORACLE_RADIO_PROMPT },
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
