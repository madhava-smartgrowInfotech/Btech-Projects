import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { motion } from "motion/react";
import { Accessibility, CalendarClock, Download, MapPin, QrCode, Search, SearchX, Timer } from "lucide-react";
import { HallLayoutPreview } from "@/components/halls/HallLayoutPreview";
import { PublicShell } from "@/components/layout/PublicShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { api, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/format";

interface LookupSeat {
  plan_id: number;
  session: { label: string; date: string; start_time: string; end_time: string };
  status: "today" | "upcoming" | "completed";
  course: { code: string; name: string };
  hall: { code: string; name: string; where: string; rows: number; cols: number; blocked: string[]; accessible: string[]; aisles: number[] };
  seat: { label: string; row: number; col: number; accessible: boolean };
}

interface LookupResult {
  candidate: { roll_no: string; name: string };
  seats: LookupSeat[];
}

const STATUS = {
  today: <Badge variant="success"><Timer /> Today</Badge>,
  upcoming: <Badge><CalendarClock /> Upcoming</Badge>,
  completed: <Badge variant="secondary">Completed</Badge>,
};

function SeatCard({ seat, roll, index }: { seat: LookupSeat; roll: string; index: number }) {
  const slip = `/api/public/slip/${encodeURIComponent(roll)}/${seat.plan_id}.pdf`;
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 * index, duration: 0.35 }}>
      <Card className={seat.status === "completed" ? "opacity-70" : undefined}>
        <CardContent className="grid gap-6 p-5 sm:p-6 md:grid-cols-[1fr_16rem] md:items-center">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              {STATUS[seat.status]}
              <span className="text-sm text-muted-foreground">
                {formatDate(seat.session.date)} · {seat.session.start_time}-{seat.session.end_time}
              </span>
            </div>
            <div>
              <div className="font-mono text-sm text-muted-foreground">{seat.course.code}</div>
              <div className="text-lg font-semibold">{seat.course.name}</div>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <div className="rounded-2xl bg-primary px-5 py-3 text-primary-foreground shadow-lift">
                <div className="text-2xs font-semibold uppercase tracking-widest opacity-80">Seat</div>
                <div className="font-display text-4xl font-semibold leading-none">{seat.seat.label}</div>
              </div>
              <div>
                <div className="font-semibold">
                  {seat.hall.code} · {seat.hall.name}
                </div>
                {seat.hall.where && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <MapPin className="size-3.5" /> {seat.hall.where}
                  </div>
                )}
                {seat.seat.accessible && (
                  <div className="mt-1 flex items-center gap-1 text-sm text-success">
                    <Accessibility className="size-4" /> Accessible seat
                  </div>
                )}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild>
                <a href={slip} download>
                  <Download /> Seat slip (PDF)
                </a>
              </Button>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline">
                    <QrCode /> QR code
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-64 text-center">
                  <img src={`/api/public/qr/${encodeURIComponent(roll)}.png`} alt={`QR code for ${roll}`} className="mx-auto size-48 rounded-lg bg-white p-2" />
                  <p className="mt-2 text-xs text-muted-foreground">The invigilator can scan this to mark you present.</p>
                </PopoverContent>
              </Popover>
            </div>
          </div>
          <div className="rounded-xl border bg-muted/30 p-4">
            <HallLayoutPreview
              rows={seat.hall.rows}
              cols={seat.hall.cols}
              blocked={seat.hall.blocked}
              accessible={seat.hall.accessible}
              aisles={seat.hall.aisles}
              highlight={seat.seat.label}
            />
            <p className="mt-2 text-center text-xs text-muted-foreground">
              Row {seat.seat.label.replace(/\d+$/, "")}, seat {seat.seat.col + 1} from the left, facing the front
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function LookupPage() {
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const [value, setValue] = useState(candidateId ?? "");
  useEffect(() => setValue(candidateId ?? ""), [candidateId]);

  const lookup = useQuery({
    queryKey: ["lookup", candidateId],
    queryFn: async () => (await api.get<LookupResult>(`/public/lookup/${encodeURIComponent(candidateId!)}`)).data,
    enabled: Boolean(candidateId),
    retry: false,
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    const id = value.trim().toUpperCase();
    if (id) navigate(`/lookup/${encodeURIComponent(id)}`);
  }

  const notFound = axios.isAxiosError(lookup.error) && lookup.error.response?.status === 404;

  return (
    <PublicShell>
      <section className="relative overflow-hidden border-b bg-grid">
        <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background/80 to-background" />
        <div className="container relative py-14 sm:py-20">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-2xl text-center">
            <h1 className="font-display text-4xl font-semibold text-balance sm:text-5xl">Find your seat</h1>
            <p className="mt-3 text-muted-foreground">Enter your candidate ID (roll number) to see your hall and seat for every published exam.</p>
            <form onSubmit={submit} className="mx-auto mt-8 flex max-w-lg flex-col gap-2 sm:flex-row">
              <Input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Candidate ID, e.g. ACF24017"
                className="h-12 text-base"
                aria-label="Candidate ID"
                autoComplete="off"
                autoCapitalize="characters"
                spellCheck={false}
              />
              <Button type="submit" size="lg" className="h-12" disabled={!value.trim()} loading={lookup.isFetching}>
                <Search /> Find my seat
              </Button>
            </form>
          </motion.div>
        </div>
      </section>

      <section className="container max-w-4xl py-10">
        {lookup.isPending && candidateId && (
          <div className="space-y-4">
            <Skeleton className="h-64 w-full rounded-xl" />
          </div>
        )}
        {lookup.isError && (
          <Card className="mx-auto max-w-lg">
            <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
              <SearchX className="size-10 text-muted-foreground" />
              <div className="font-semibold">{notFound ? "No seat found yet" : "Something went wrong"}</div>
              <p className="text-sm text-muted-foreground">{errorMessage(lookup.error)}</p>
            </CardContent>
          </Card>
        )}
        {lookup.data && (
          <div className="space-y-5">
            <div>
              <h2 className="font-display text-2xl font-semibold">Hi {lookup.data.candidate.name}</h2>
              <p className="text-sm text-muted-foreground">
                {lookup.data.seats.length === 1 ? "Your seat" : `Your ${lookup.data.seats.length} seats`} for {lookup.data.candidate.roll_no}.
                Plans can still change until the day before, so check again before you travel.
              </p>
            </div>
            {lookup.data.seats.map((s, i) => (
              <SeatCard key={s.plan_id} seat={s} roll={lookup.data!.candidate.roll_no} index={i} />
            ))}
          </div>
        )}
        {!candidateId && (
          <div className="mx-auto grid max-w-3xl gap-4 text-sm text-muted-foreground sm:grid-cols-3">
            {[
              ["Your ID", "It is printed on your admission letter and seat slip."],
              ["Your seat", "Hall, building and seat - with a map of where it is in the room."],
              ["Your slip", "Download a slip with a QR code. Invigilators scan it at the door."],
            ].map(([title, text]) => (
              <div key={title} className="rounded-xl border p-4">
                <div className="font-medium text-foreground">{title}</div>
                <div className="mt-1">{text}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </PublicShell>
  );
}
