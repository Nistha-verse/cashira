import type { ButtonHTMLAttributes, HTMLAttributes, InputHTMLAttributes } from "react";

export function Button({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) { return <button className={`button ${className}`} {...props} />; }
export function Card({ className = "", ...props }: HTMLAttributes<HTMLElement>) { return <section className={`card ${className}`} {...props} />; }
export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) { return <input className={`line-input ${className}`} {...props} />; }
export function Select({ className = "", ...props }: InputHTMLAttributes<HTMLSelectElement>) { return <select className={`line-input ${className}`} {...props} />; }
export function AsyncState({ message, error, onRetry }: { message?: string; error?: string; onRetry?: () => void }) { if (error) return <div className="state error-state" role="alert"><strong>{error}</strong>{onRetry && <Button onClick={onRetry}>{"Try again"}</Button>}</div>; return <div className="state" aria-live="polite">{message || "Loading the latest view…"}</div>; }
