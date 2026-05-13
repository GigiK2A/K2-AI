"use client";

import { useState } from "react";
import { Star } from "lucide-react";

export function FeedbackWidget({
  onSubmit,
}: {
  reportId: string;
  onSubmit: (rating: number, comment: string) => Promise<void>;
}) {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  if (submitted) {
    return <p className="mt-3 text-xs text-[var(--text-muted)]">Grazie per il feedback!</p>;
  }

  return (
    <div className="mt-4 rounded-xl border border-[var(--line)] p-3">
      <p className="mb-2 text-xs text-[var(--text-soft)]">Come valuteresti questo report?</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => setRating(star)}
            onMouseEnter={() => setHover(star)}
            onMouseLeave={() => setHover(0)}
          >
            <Star
              size={18}
              className={(hover || rating) >= star ? "fill-[var(--teal)] text-[var(--teal)]" : "text-[var(--line)]"}
            />
          </button>
        ))}
      </div>
      {rating > 0 && (
        <>
          <textarea
            className="mt-2 w-full rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs text-[var(--text-main)] placeholder:text-[var(--text-muted)] focus:outline-none"
            placeholder="Cosa miglioreresti? (opzionale)"
            rows={2}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <button
            onClick={async () => {
              setLoading(true);
              await onSubmit(rating, comment);
              setSubmitted(true);
              setLoading(false);
            }}
            disabled={loading}
            className="mt-1.5 rounded-lg bg-[var(--teal)] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50"
          >
            {loading ? "Invio..." : "Invia feedback"}
          </button>
        </>
      )}
    </div>
  );
}
