import { error } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions = {
  getPlaylistInfo: async ({ request }) => {
    try {
      const data = await request.formData();
      const url = data.get('url');

      if (!url || typeof url !== 'string') {
        throw error(400, 'URL is required');
      }

      if (!url.includes('youtube.com/playlist')) {
        throw error(400, 'Invalid YouTube playlist URL');
      }

      // Make the actual API request to your backend
      const response = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/v1/playlist/info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw error(response.status, 'Failed to fetch playlist information');
      }

      const playlistInfo = await response.json();
      return {
        success: true,
        data: playlistInfo,
      };
    } catch (err) {
      console.error('Error fetching playlist info:', err);
      throw error(500, 'Failed to fetch playlist information');
    }
  }
} satisfies Actions;