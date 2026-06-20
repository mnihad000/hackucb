import type { PropsWithChildren, ReactNode } from "react";

type SectionProps = PropsWithChildren<{
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}>;

export default function Section({
  eyebrow,
  title,
  description,
  action,
  className = "",
  children,
}: SectionProps) {
  return (
    <section className={`px-4 sm:px-6 lg:px-8 ${className}`.trim()}>
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl">
            {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
            <h2 className="section-title mt-4">{title}</h2>
            {description ? <p className="section-copy mt-4">{description}</p> : null}
          </div>
          {action}
        </div>
        {children}
      </div>
    </section>
  );
}
