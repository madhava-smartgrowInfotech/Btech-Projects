import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LocateFixed } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, apiError } from "@/lib/api";
import type { ComplaintDetail } from "@/lib/complaints";

/** Report a coverage problem at a location. The server attaches the evidence already measured in that zone. */
export function ReportDialog({ open, onOpenChange, at, operator }: { open: boolean; onOpenChange: (o: boolean) => void; at?: [number, number] | null; operator?: string | null }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [pos, setPos] = useState<[number, number] | null>(at ?? null);
  const [op, setOp] = useState(operator ?? "");
  const [note, setNote] = useState("");
  const [locating, setLocating] = useState(false);
  useEffect(() => {
    if (open) {
      setPos(at ?? null);
      setOp(operator ?? "");
      setNote("");
    }
  }, [open, at, operator]);

  const locate = () => {
    if (!navigator.geolocation) return toast.error("Location is not available in this browser");
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (p) => { setPos([p.coords.latitude, p.coords.longitude]); setLocating(false); },
      () => { toast.error("Couldn't get your location"); setLocating(false); },
      { enableHighAccuracy: true, timeout: 12000 },
    );
  };
  const send = useMutation({
    mutationFn: async () => (await api.post<ComplaintDetail>("/api/complaints", { lat: pos![0], lon: pos![1], operator: op.trim() || null, note: note.trim() })).data,
    onSuccess: (c) => {
      toast.success(`Complaint ${c.ref_code} registered`);
      qc.invalidateQueries({ queryKey: ["complaints"] });
      onOpenChange(false);
      navigate(`/app/complaints/${c.id}`);
    },
    onError: (e) => toast.error(apiError(e)),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="z-[1300]">
        <DialogHeader>
          <DialogTitle>Report a coverage problem</DialogTitle>
          <DialogDescription>SignalScout attaches every reading already measured in this zone as evidence and registers the complaint with the operator desk.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Location</Label>
            <div className="flex items-center gap-2">
              <Input readOnly value={pos ? `${pos[0].toFixed(5)}, ${pos[1].toFixed(5)}` : ""} placeholder="Use your current location" />
              <Button type="button" variant="outline" onClick={locate} loading={locating} aria-label="Use my location"><LocateFixed /></Button>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="rep-op">Operator</Label>
            <Input id="rep-op" value={op} onChange={(e) => setOp(e.target.value)} placeholder="Detected from nearby readings if empty" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="rep-note">What happens here?</Label>
            <Textarea id="rep-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Calls drop and mobile data stops working near the bus stand" maxLength={2000} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={() => send.mutate()} disabled={!pos || note.trim().length < 3} loading={send.isPending}>Register complaint</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
