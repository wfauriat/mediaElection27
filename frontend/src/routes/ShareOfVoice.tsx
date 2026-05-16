import { Layout } from "@/components/Layout";

export default function ShareOfVoice() {
  return (
    <Layout>
      <ComingSoon name="Part de voix" />
    </Layout>
  );
}

function ComingSoon({ name }: { name: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
      {name} — à venir
    </div>
  );
}
