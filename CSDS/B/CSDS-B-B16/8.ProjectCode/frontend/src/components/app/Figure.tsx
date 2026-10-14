/** A square image with a caption. Missing images show a labelled placeholder instead of a broken icon. */
export function Figure({ src, caption, alt }: { src: string | null | undefined; caption: string; alt?: string }) {
  return (
    <figure className="min-w-0">
      <div className="glass overflow-hidden rounded-xl">
        {src ? (
          <img src={src} alt={alt ?? caption} loading="lazy" className="aspect-square w-full bg-black object-cover" />
        ) : (
          <div role="img" aria-label={`${caption} not available`} className="grid aspect-square w-full place-items-center text-xs text-muted-foreground">
            Not available
          </div>
        )}
      </div>
      <figcaption className="mt-1.5 text-center text-xs text-muted-foreground">{caption}</figcaption>
    </figure>
  );
}
