import React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function MultiSelect({ options = [], value = [], onChange, placeholder = "Pilih...", testid }) {
  const toggle = (v) => {
    if (value.includes(v)) onChange(value.filter((x) => x !== v));
    else onChange([...value, v]);
  };
  const label =
    value.length === 0 ? placeholder : `${value.length} dipilih`;
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          type="button" variant="outline"
          className="w-full justify-between font-normal border-slate-200"
          data-testid={testid}
        >
          <span className={value.length ? "text-slate-800" : "text-slate-400"}>{label}</span>
          <ChevronsUpDown size={15} className="text-slate-400" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-1" align="start">
        <ScrollArea className="max-h-56">
          {options.length === 0 && <p className="text-xs text-slate-400 p-3">Tidak ada opsi</p>}
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => toggle(opt.value)}
              className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-slate-100 text-left"
              data-testid={`${testid}-opt-${opt.value}`}
            >
              <span className={`flex h-4 w-4 items-center justify-center rounded border ${value.includes(opt.value) ? "bg-emerald-700 border-emerald-700 text-white" : "border-slate-300"}`}>
                {value.includes(opt.value) && <Check size={12} />}
              </span>
              {opt.label}
            </button>
          ))}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
