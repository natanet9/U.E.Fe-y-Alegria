import { useState, useCallback, useRef } from "react";

export function useDialog() {
  const [dialog, setDialog] = useState({ isOpen: false, mode: "confirm", message: "", iconType: "info", title: "", inputPlaceholder: "", inputValue: "" });
  const resolveRef = useRef(null);

  const confirm = useCallback((message, { iconType = "warning", title = "Confirmar" } = {}) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setDialog({ isOpen: true, mode: "confirm", message, iconType, title, inputPlaceholder: "", inputValue: "" });
    });
  }, []);

  const prompt = useCallback((message, { iconType = "info", title = "Información", placeholder = "" } = {}) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setDialog({ isOpen: true, mode: "prompt", message, iconType, title, inputPlaceholder: placeholder, inputValue: "" });
    });
  }, []);

  const handleConfirm = useCallback((value) => {
    setDialog((prev) => ({ ...prev, isOpen: false }));
    if (resolveRef.current) resolveRef.current(value !== undefined ? value : true);
  }, []);

  const handleCancel = useCallback(() => {
    setDialog((prev) => ({ ...prev, isOpen: false }));
    if (resolveRef.current) resolveRef.current(false);
  }, []);

  return { dialog, confirm, prompt, handleConfirm, handleCancel };
}
