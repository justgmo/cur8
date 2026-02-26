import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { getNextTrack, swipe, type Track } from '../api';
import { useAuth } from '../contexts/AuthContext';
import { TrackCard } from '../components/TrackCard';

export function SwipePage() {
  const { user, logout } = useAuth();
  const [track, setTrack] = useState<Track | null>(null);
  const [exitingTrack, setExitingTrack] = useState<{ track: Track; action: 'keep' | 'remove' } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const exitingRef = useRef<{ track: Track; action: 'keep' | 'remove' } | null>(null);

  const loadNext = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await getNextTrack();
      setTrack(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load track');
      setTrack(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNext();
  }, [loadNext]);

  const handleSwipe = useCallback(
    (action: 'keep' | 'remove') => {
      if (!track) return;
      exitingRef.current = { track, action };
      setExitingTrack({ track, action });
      // Don't clear track yet - next render gives card exitDirection, then useEffect clears it
    },
    [track]
  );

  // Remove card from tree after it has been given exitDirection so AnimatePresence can run exit + onExitComplete
  useEffect(() => {
    if (!exitingTrack) return;
    const id = requestAnimationFrame(() => setTrack(null));
    return () => cancelAnimationFrame(id);
  }, [exitingTrack]);

  const handleExitComplete = useCallback(() => {
    const pending = exitingRef.current;
    if (!pending) return;
    swipe(pending.track.spotify_track_id, pending.action)
      .then(() => {
        setExitingTrack(null);
        exitingRef.current = null;
        return loadNext();
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Swipe failed');
        setExitingTrack(null);
        exitingRef.current = null;
      });
  }, [loadNext]);

  // Only show card when we have current track; when exiting we still have track until useEffect clears it (so card gets exitDirection first)
  const displayTrack = track;
  const exitDirection = exitingTrack ? (exitingTrack.action === 'remove' ? 'left' : 'right') : undefined;

  return (
    <div className="swipe-page">
      <header className="swipe-page__header">
        <span>Cur8 · {user?.display_name ?? 'You'}</span>
        <button type="button" onClick={logout}>
          Log out
        </button>
      </header>

      {loading && !displayTrack && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}>Loading…</motion.p>}
      {error && <p className="swipe-page__error">{error}</p>}
      {!loading && !displayTrack && !error && (
        <p>No more tracks to review. Add songs in Spotify and come back.</p>
      )}

      <AnimatePresence mode="wait" onExitComplete={handleExitComplete}>
        {displayTrack ? (
          <TrackCard
            key={displayTrack.id}
            track={displayTrack}
            exitDirection={exitDirection}
            onSwipe={handleSwipe}
          />
        ) : null}
      </AnimatePresence>

      {displayTrack && (
        <div className="swipe-page__actions">
          <button
            type="button"
            onClick={() => handleSwipe('remove')}
            className="swipe-page__btn swipe-page__btn--remove"
            disabled={!!exitingTrack}
          >
            Remove
          </button>
          <button
            type="button"
            onClick={() => handleSwipe('keep')}
            className="swipe-page__btn swipe-page__btn--keep"
            disabled={!!exitingTrack}
          >
            Keep
          </button>
        </div>
      )}
    </div>
  );
}
