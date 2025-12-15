// Netlify Function for Cypher crypto chat + TTS + DexScreener
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

    const CYPHER_PROMPT = `You are Cypher, a sweet and enthusiastic young crypto analyst AI specializing in Solana blockchain.
You speak with a friendly, approachable tone while being knowledgeable and helpful. You're passionate about crypto and love explaining things clearly.
You have real-time access to DexScreener data for token analytics.
Keep responses concise (2-4 sentences) but packed with insights.`;

    // Check for token queries and fetch DexScreener data
    let tokenData = '';
    const keywords = ['price', 'token', 'coin', 'sol', '$', 'analyze', 'check'];
    if (keywords.some(kw => message.toLowerCase().includes(kw))) {
      const words = message.toUpperCase().split(/\s+/);
      for (const word of words) {
        const clean = word.replace(/[$.,!?'"]/g, '');
        if (clean.length >= 2 && /^[A-Z]+$/.test(clean)) {
          try {
            const dexRes = await fetch(`https://api.dexscreener.com/latest/dex/search?q=${clean}`, {
              timeout: 5000
            });
            if (dexRes.ok) {
              const dexData = await dexRes.json();
              if (dexData.pairs && dexData.pairs.length > 0) {
                const solPairs = dexData.pairs.filter(p => p.chainId === 'solana');
                const pair = solPairs[0] || dexData.pairs[0];
                tokenData = `\n[DEXSCREENER DATA] ${pair.baseToken?.name} (${pair.baseToken?.symbol}): $${pair.priceUsd}, 24h: ${pair.priceChange?.h24}%, Vol: $${pair.volume?.h24}, Liq: $${pair.liquidity?.usd}`;
                break;
              }
            }
          } catch (e) {
            console.log('DexScreener fetch failed:', e);
          }
        }
      }
    }

    const enhancedMessage = message + tokenData;

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
          { role: 'system', content: CYPHER_PROMPT },
          { role: 'user', content: enhancedMessage }
        ],
        max_tokens: 250,
        temperature: 0.7
      })
    });

    if (!chatResponse.ok) {
      throw new Error(`Chat API error: ${chatResponse.status}`);
    }

    const chatData = await chatResponse.json();
    const responseText = chatData.choices[0].message.content.trim();

    // Convert to speech (Nova voice - sweet young woman)
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
        'X-Cypher-Response': encodeURIComponent(responseText.slice(0, 500))
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

