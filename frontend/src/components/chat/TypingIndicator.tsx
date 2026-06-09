import EmiAvatar from './EmiAvatar';

export default function TypingIndicator() {
  return (
    <div className="flex gap-2.5 justify-start">
      <div className="flex-shrink-0 mt-1">
        <EmiAvatar size={36} state="typing" />
      </div>
      <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-md px-4 py-3">
        <div className="flex gap-1.5 items-center">
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

