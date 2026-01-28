export default async function handler(req, res) {
  const RENDER_URL = process.env.RENDER_URL || 'https://n8n-automation.onrender.com';
  
  try {
    // Ping the Render service
    const response = await fetch(RENDER_URL, {
      method: 'GET',
      headers: {
        'User-Agent': 'Vercel-KeepAlive/1.0',
        'Accept': 'text/html,application/json'
      },
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });
    
    const status = response.status;
    const statusText = response.statusText;
    const contentType = response.headers.get('content-type');
    
    return res.status(200).json({
      success: true,
      message: 'Ping successful',
      renderUrl: RENDER_URL,
      status: status,
      statusText: statusText,
      contentType: contentType,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    // Even if ping fails, return success (Render might be starting up)
    return res.status(200).json({
      success: false,
      message: 'Ping failed but keep-alive attempted',
      error: error.message,
      renderUrl: RENDER_URL,
      timestamp: new Date().toISOString(),
      note: 'This is normal if Render service is starting up'
    });
  }
}
