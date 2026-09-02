function InfoPanel() {
  return (
    <section className="rounded-2xl bg-brand-600 px-8 py-10 md:px-10 md:py-12 flex flex-col items-center text-center shadow-panel">
      <img
        className="w-24 h-24 object-contain mb-4"
        loading="lazy"
        alt="Logo Unidad Educativa Republica de Panama"
        src="/assets/login/logo-Colegio.png"
      />

      <h1 className="m-0 text-white text-4xl md:text-5xl font-bold tracking-wide">
        Sistema Academico
      </h1>

      <p className="m-0 mt-3 text-white/95 text-base md:text-lg leading-relaxed max-w-xl">
        Gestion educativa integral para estudiantes, docentes y administracion.
      </p>

      <img
        className="hidden sm:block mt-8 w-full max-w-[560px] rounded-xl object-cover"
        loading="lazy"
        alt="Estudiantes en aula"
        src="/assets/login/students.png"
      />
    </section>
  );
}

export default InfoPanel;
