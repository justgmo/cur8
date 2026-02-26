import { useMotionValue, useTransform, motion } from 'framer-motion';
import type { Track } from '../api';

const SWIPE_THRESHOLD = 80;
const VELOCITY_THRESHOLD = 400;
const ROTATION_RANGE = 12;

interface TrackCardProps {
  track: Track;
  exitDirection?: 'left' | 'right';
  onSwipe?: (action: 'keep' | 'remove') => void;
}

export function TrackCard({ track, exitDirection, onSwipe }: TrackCardProps) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 0, 200], [-ROTATION_RANGE, 0, ROTATION_RANGE]);

  const exitOffset = 500;
  const exitY = 120;
  const exitVariants = {
    left: { x: -exitOffset, y: exitY, opacity: 0, rotate: -15 },
    right: { x: exitOffset, y: -exitY, opacity: 0, rotate: 15 },
  };
  const exitVariant = exitDirection ? exitVariants[exitDirection] : { opacity: 0, x: 0 };

  const handleDragEnd = (
    _: MouseEvent | TouchEvent | PointerEvent,
    info: { offset: { x: number }; velocity: { x: number } }
  ) => {
    const offsetX = info.offset.x;
    const velocityX = info.velocity.x;
    if (offsetX > SWIPE_THRESHOLD || velocityX > VELOCITY_THRESHOLD) {
      onSwipe?.('keep');
    } else if (offsetX < -SWIPE_THRESHOLD || velocityX < -VELOCITY_THRESHOLD) {
      onSwipe?.('remove');
    } else {
      x.set(0);
    }
  };

  return (
    <motion.article
      className="track-card"
      layout
      style={{ x, rotate }}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{
        ...exitVariant,
        transition: { duration: 0.3, ease: 'easeIn' },
      }}
      transition={{ duration: 0.2 }}
      drag="x"
      dragConstraints={{ left: -400, right: 400 }}
      dragElastic={0.6}
      onDragEnd={onSwipe ? handleDragEnd : undefined}
    >
      {track.artwork_url && (
        <img src={track.artwork_url} alt="" className="track-card__artwork" />
      )}
      <h2 className="track-card__name">{track.name}</h2>
      {track.artists && <p className="track-card__artists">{track.artists}</p>}
      {track.album_name && <p className="track-card__album">{track.album_name}</p>}
      <div className="track-card__preview-wrap">
        {track.preview_url ? (
          <>
            <span className="track-card__preview-label">Preview</span>
            <audio src={track.preview_url} controls className="track-card__preview" />
          </>
        ) : (
          <span className="track-card__preview-unavailable">No preview</span>
        )}
      </div>
    </motion.article>
  );
}
