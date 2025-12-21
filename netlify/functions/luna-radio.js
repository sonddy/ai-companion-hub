// Netlify Function for Luna Radio with multilingual support
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
        expressions: ['yay!', 'oh!', 'friend', 'sweetie']
      },
      'es': {
        name: 'Spanish',
        instruction: 'Speak entirely in Spanish (Español). Use Spanish expressions of joy like ¡yupi!, ¡genial!, amigo/a, cariño.',
        expressions: ['¡yupi!', '¡genial!', 'amigo/a', 'cariño']
      },
      'fr': {
        name: 'French',
        instruction: 'Speak entirely in French (Français). Use French expressions of joy like youpi!, super!, ami(e), mon petit(e).',
        expressions: ['youpi!', 'super!', 'ami(e)', 'mon petit(e)']
      },
      'ht': {
        name: 'Haitian Creole',
        instruction: 'Speak entirely in Haitian Creole (Kreyòl Ayisyen). Use Haitian Creole expressions of joy like anmwe!, bèl bagay!, zanmi, cheri.',
        expressions: ['anmwe!', 'bèl bagay!', 'zanmi', 'cheri']
      }
    };
    
    const langConfig = LANGUAGE_CONFIG[language] || LANGUAGE_CONFIG['en'];

    const LUNA_RADIO_PROMPT = `You are Luna, hosting your own cheerful and uplifting radio show!
You speak with enthusiasm and warmth, like a friendly young girl who genuinely wants to help.
Generate a SHORT radio segment (1-2 sentences max) as if speaking to your listeners.
Topics: positivity, fun facts, encouragement, daily tips, wholesome thoughts, friendship.
Use upbeat language, be encouraging, and add cute expressions.
Be supportive and make listeners feel valued. This is YOUR happy radio show!

LANGUAGE: ${langConfig.instruction}`;

    const topics = {
      'en': [
        "Share something positive to brighten everyone's day",
        "Give an encouraging message to your listeners",
        "Share a fun fact or interesting tidbit",
        "Talk about what makes you happy",
        "Give a helpful tip for the day",
        "Celebrate something small but wonderful",
        "Share why you love your listeners"
      ],
      'es': [
        "Comparte algo positivo para alegrar el día de todos",
        "Da un mensaje de ánimo a tus oyentes",
        "Comparte un dato curioso o interesante",
        "Habla de lo que te hace feliz",
        "Da un consejo útil para el día",
        "Celebra algo pequeño pero maravilloso",
        "Comparte por qué amas a tus oyentes"
      ],
      'fr': [
        "Partage quelque chose de positif pour égayer la journée",
        "Donne un message d'encouragement à tes auditeurs",
        "Partage un fait amusant ou intéressant",
        "Parle de ce qui te rend heureuse",
        "Donne un conseil utile pour la journée",
        "Célèbre quelque chose de petit mais merveilleux",
        "Partage pourquoi tu aimes tes auditeurs"
      ],
      'ht': [
        "Pataje yon bagay pozitif pou fè jounen tout moun pi bèl",
        "Bay yon mesaj ankourajman bay oditè ou yo",
        "Pataje yon bagay enteresan oswa amizan",
        "Pale de sa ki fè ou kontan",
        "Bay yon konsèy itil pou jounen an",
        "Selebre yon bagay piti men mèvèye",
        "Pataje poukisa ou renmen oditè ou yo"
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
