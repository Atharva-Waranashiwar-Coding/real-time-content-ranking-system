type StateBlockProps = {
  title: string;
  description: string;
  tone?: "default" | "error";
};

export function StateBlock({ title, description, tone = "default" }: StateBlockProps) {
  const toneClassName =
    tone === "error"
      ? "border-rose-200 bg-rose-50/90 text-rose-900"
      : "border-[color:var(--border-subtle)] bg-[color:var(--surface-muted)] text-[color:var(--ink-soft)]";

  return (
    <div className={`rounded-[24px] border px-5 py-8 ${toneClassName}`}>
      <p className="font-heading text-xl">{title}</p>
      <p className="mt-2 max-w-xl text-sm leading-6">{description}</p>
    </div>
  );
}
