import { FormField, Input } from "@/components/ui/Field";
import { Select } from "@/components/ui/Select";
import { CLINICAL_FIELDS, type ClinicalKey, type ClinicalValues } from "@/lib/clinical";

interface ClinicalFormProps {
  value: ClinicalValues;
  onChange: (value: ClinicalValues) => void;
  disabled?: boolean;
  idPrefix?: string;
}

/** The 13 heart-model inputs. Coded fields are selects; numeric fields use the model's valid ranges. */
export function ClinicalForm({ value, onChange, disabled, idPrefix = "clinical" }: ClinicalFormProps) {
  const set = (key: ClinicalKey, next: number | string) => onChange({ ...value, [key]: next });
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {CLINICAL_FIELDS.map((field) => (
        <FormField key={field.key} id={`${idPrefix}-${field.key}`} label={field.label}>
          {({ id, ...aria }) =>
            field.options ? (
              <Select
                id={id}
                aria-label={field.label}
                aria-describedby={aria["aria-describedby"]}
                value={String(value[field.key])}
                onValueChange={(v) => set(field.key, Number(v))}
                options={field.options.map(([code, text]) => ({ value: String(code), label: text }))}
                disabled={disabled}
              />
            ) : (
              <Input
                id={id}
                {...aria}
                type="number"
                required
                inputMode="decimal"
                min={field.min}
                max={field.max}
                step={field.step ?? 1}
                value={value[field.key]}
                disabled={disabled}
                onChange={(e) => set(field.key, e.target.value)}
              />
            )
          }
        </FormField>
      ))}
    </div>
  );
}
