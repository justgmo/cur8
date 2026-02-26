const API_URL = import.meta.env.VITE_API_URL

export interface User {
    id: string;
    spotify_user_id: string;
    display_name: string | null;
    avatar_url: string | null;
}

export interface Track {
  id: string;
  spotify_track_id: string;
  name: string;
  artists: string | null;
  album_name: string | null;
  artwork_url: string | null;
  preview_url: string | null;
  duration_ms: number | null;
}

async function request<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const res = await fetch(`${API_URL}${path}`, {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    ...options,
    });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? res.statusText);
    }
    if (res.status === 204) return undefined as T;
    return res.json();
}

export async function getMe(): Promise<User> {
    return request<User>('/auth/me');
}

export async function getLoginUrl(): Promise<{ authorization_url: string }> {
    return request<{ authorization_url: string }>('/auth/login');
}

export async function logout(): Promise<void> {
    await request<{ status: string }>('/auth/logout', { method: 'POST' });
}

export async function getNextTrack(): Promise<Track | null> {
    return request<Track | null>('/tracks/next');
}

export async function swipe(
    spotifyTrackId: string,
    action: 'keep' | 'remove'
): Promise<{ status: string }> {
    return request<{ status: string }>('/tracks/swipe', {
        method: 'POST',
        body: JSON.stringify({ spotify_track_id: spotifyTrackId, action }),
    });
}
