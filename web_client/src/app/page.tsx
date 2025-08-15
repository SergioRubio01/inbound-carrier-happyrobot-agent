/**
 * @file: page.tsx
 * @description: Modern startup-style landing page for HappyRobot - Document Processing Platform
 * @author HappyRobot Team
 * @created 2025-06-16
 * @lastModified 2025-07-29
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, useScroll, useTransform, AnimatePresence, useInView, useSpring, useMotionValue } from 'framer-motion';
import { useTranslation } from '@/lib/i18n/useTranslation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  FileCheck,
  Zap,
  Shield,
  BarChart3,
  FileText,
  Clock,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Globe,
  Layers,
  Users,
  TrendingUp,
  Award,
  Star,
  Code2,
  Cloud,
  Database,
  Bot,
  ChevronRight,
  Play,
  Building,
  Cpu,
  Workflow,
  X,
  PlayCircle
} from 'lucide-react';
import { LandingFooter } from '@/components/landing-footer';
import { LandingHeader } from '@/components/landing-header';

// Modern gradient mesh background
function GradientMesh() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      <div className="absolute -inset-[10px] opacity-50">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-bizai-accent1 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-bizai-accent2 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>
    </div>
  );
}

// Animated particles background
function ParticleField() {
  // Use deterministic values based on index to avoid hydration mismatch
  const particles = Array.from({ length: 20 }, (_, i) => {
    // Create pseudo-random but deterministic values based on index
    const hash = (i * 2654435761) % 2147483647;
    const normalizedHash = hash / 2147483647;

    return {
      id: i,
      size: (normalizedHash * 4 + 1).toFixed(2),
      x: ((hash % 100) + (i * 5.263)) % 100,
      y: ((hash % 87) + (i * 7.129)) % 100,
      duration: (normalizedHash * 20 + 10).toFixed(1),
      delay: (i * 0.3) % 5,
    };
  });

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full bg-bizai-accent1/20"
          style={{
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          animate={{
            y: [0, -30, 0],
            x: [0, 10, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: parseFloat(particle.duration),
            repeat: Infinity,
            ease: 'easeInOut',
            delay: particle.delay,
          }}
        />
      ))}
    </div>
  );
}

// 3D floating cards animation
function FloatingCard({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useSpring(useTransform(y, [-100, 100], [10, -10]));
  const rotateY = useSpring(useTransform(x, [-100, 100], [-10, 10]));

  function handleMouse(event: React.MouseEvent<HTMLDivElement>) {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    x.set(event.clientX - centerX);
    y.set(event.clientY - centerY);
  }

  function handleMouseLeave() {
    x.set(0);
    y.set(0);
  }

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      onMouseMove={handleMouse}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d',
      }}
      className="relative"
    >
      {children}
    </motion.div>
  );
}

// Animated counter component
function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      const interval = setInterval(() => {
        setCount(prev => {
          if (prev >= value) {
            clearInterval(interval);
            return value;
          }
          return prev + Math.ceil(value / 50);
        });
      }, 30);
      return () => clearInterval(interval);
    }
  }, [isInView, value]);

  return (
    <span ref={ref} className="tabular-nums">
      {count}{suffix}
    </span>
  );
}

export default function HomePage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [hoveredFeature, setHoveredFeature] = useState<number | null>(null);
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [showDemoModal, setShowDemoModal] = useState(false);
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: containerRef });

  // Parallax effects
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 200]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  const features = [
    {
      icon: FileCheck,
      title: t('landing', 'feature1Title'),
      description: t('landing', 'feature1Description'),
      gradient: 'from-purple-500 to-pink-500',
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10'
    },
    {
      icon: Zap,
      title: t('landing', 'feature2Title'),
      description: t('landing', 'feature2Description'),
      gradient: 'from-yellow-400 to-orange-500',
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10'
    },
    {
      icon: Shield,
      title: t('landing', 'feature3Title'),
      description: t('landing', 'feature3Description'),
      gradient: 'from-green-500 to-teal-500',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10'
    },
    {
      icon: BarChart3,
      title: t('landing', 'feature4Title'),
      description: t('landing', 'feature4Description'),
      gradient: 'from-blue-500 to-cyan-500',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10'
    },
    {
      icon: Bot,
      title: 'AI-Powered Intelligence',
      description: 'Advanced machine learning for smart document understanding',
      gradient: 'from-indigo-500 to-purple-500',
      color: 'text-indigo-500',
      bgColor: 'bg-indigo-500/10'
    },
    {
      icon: Workflow,
      title: 'Automated Workflows',
      description: 'Build custom automation pipelines with visual workflow designer',
      gradient: 'from-pink-500 to-rose-500',
      color: 'text-pink-500',
      bgColor: 'bg-pink-500/10'
    }
  ];

  const stats = [
    { value: 500000, suffix: '+', label: 'Documents Processed' },
    { value: 90, suffix: '%', label: 'Accuracy Rate' },
    { value: 2, suffix: '+', label: 'Enterprise Clients' },
    { value: 24, suffix: '/7', label: 'Support Available' }
  ];

  const techStack = [
    { name: 'AWS Textract', icon: Cloud },
    { name: 'React', icon: Code2 },
    { name: 'TypeScript', icon: Layers },
    { name: 'PostgreSQL', icon: Database },
    { name: 'Machine Learning', icon: Cpu },
  ];

  const testimonials = [
    {
      quote: "HappyRobot transformed our document processing workflow. What used to take hours now takes minutes.",
      author: "Sarah Chen",
      role: "CFO at TechCorp",
      rating: 5
    },
    {
      quote: "The accuracy and speed of data extraction is incredible. It's like having a team of experts working 24/7.",
      author: "Michael Rodriguez",
      role: "Operations Director at FinanceHub",
      rating: 5
    },
    {
      quote: "The Excel export feature alone saved us 20 hours per week. Game-changing platform!",
      author: "Emily Watson",
      role: "Audit Manager at GlobalAudit",
      rating: 5
    }
  ];

  // Auto-rotate testimonials
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [testimonials.length]);

  return (
    <div ref={containerRef} className="relative min-h-screen w-full bg-gradient-to-b from-white via-gray-50/50 to-white dark:from-bizai-primary dark:via-gray-900 dark:to-bizai-primary overflow-x-hidden">
      {/* Modern animated background */}
      <div className="fixed inset-0 z-0">
        <GradientMesh />
        <ParticleField />
      </div>

      <LandingHeader />

      {/* Modern Hero Section with Parallax */}
      <main className="relative z-10">
        <motion.section
          style={{ y: heroY, opacity: heroOpacity }}
          className="relative min-h-screen flex items-center justify-center px-4 pt-24 pb-20"
        >
          <div className="container max-w-7xl mx-auto">
            <div className="text-center">
              {/* Animated badge */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-bizai-accent1/10 to-bizai-accent2/10 border border-bizai-accent1/20 mb-8"
              >
                <Sparkles className="w-4 h-4 text-bizai-accent1" />
                <span className="text-sm font-medium text-bizai-darkGray dark:text-gray-300">
                  Powered by AI
                </span>
              </motion.div>

              {/* Main headline with gradient text */}
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6"
              >
                <span className="bg-gradient-to-r from-bizai-accent1 via-bizai-accent2 to-bizai-yellow dark:from-bizai-accent1 dark:via-bizai-yellow dark:to-bizai-accent2 bg-clip-text text-transparent">
                  {t('landing', 'heroTitle')}
                </span>
                <br />
                <span className="text-bizai-darkGray dark:text-white">
                  {t('landing', 'heroSubtitle')}
                </span>
              </motion.h1>

              {/* Animated description */}
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="text-xl text-bizai-mediumGray dark:text-gray-300 mb-10 max-w-3xl mx-auto leading-relaxed"
              >
                {t('landing', 'heroDescription')}
              </motion.p>

              {/* CTA buttons with hover effects */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="flex flex-col sm:flex-row gap-4 justify-center items-center"
              >
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button
                    size="lg"
                    onClick={() => router.push('/login')}
                    className="group relative bg-gradient-to-r from-bizai-accent1 to-bizai-accent1/90 text-white px-8 py-6 text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden"
                  >
                    <span className="relative z-10 flex items-center">
                      {t('landing', 'getStarted')}
                      <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-bizai-accent2 to-bizai-accent1 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  </Button>
                </motion.div>

                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => setShowDemoModal(true)}
                    className="group px-8 py-6 text-lg font-semibold rounded-xl border-2 border-bizai-accent1/30 hover:border-bizai-accent1 backdrop-blur-sm bg-white/50 dark:bg-black/20 transition-all duration-300"
                  >
                    <PlayCircle className="mr-2 h-5 w-5 group-hover:text-bizai-accent1 transition-colors" />
                    Watch Demo
                  </Button>
                </motion.div>
              </motion.div>

              {/* Trust indicators */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-bizai-mediumGray"
              >
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  <span>SOC 2 Compliant</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>GDPR Ready</span>
                </div>
                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4" />
                  <span>ISO 27001 Certified</span>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.section>

        {/* Stats Section with Animated Counters */}
        <section className="py-20 relative">
          <div className="container max-w-7xl mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="text-center"
                >
                  <div className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-bizai-accent1 to-bizai-accent2 bg-clip-text text-transparent">
                    <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                  </div>
                  <p className="mt-2 text-bizai-mediumGray dark:text-gray-400">{stat.label}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Modern Bento Grid Features Section */}
        <section id="features" className="py-20 relative">
          <div className="container max-w-7xl mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl lg:text-5xl font-bold mb-4">
                <span className="bg-gradient-to-r from-bizai-accent1 to-bizai-accent2 dark:from-bizai-accent1 dark:to-bizai-yellow bg-clip-text text-transparent">
                  Powerful Features
                </span>
              </h2>
              <p className="text-xl text-bizai-mediumGray dark:text-gray-300 max-w-3xl mx-auto">
                Everything you need to automate document processing at scale
              </p>
            </motion.div>

            {/* Bento Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => (
                <FloatingCard key={index} delay={index * 0.1}>
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    className={`relative group h-full rounded-2xl p-8 backdrop-blur-sm bg-white/80 dark:bg-gray-900/80 border border-gray-200/50 dark:border-gray-700/50 shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden ${
                      index === 0 ? 'lg:col-span-2' : ''
                    }`}
                  >
                    {/* Gradient overlay on hover */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />

                    {/* Icon with gradient background */}
                    <div className={`inline-flex p-3 rounded-xl ${feature.bgColor} mb-4`}>
                      <feature.icon className={`w-8 h-8 ${feature.color}`} />
                    </div>

                    <h3 className="text-2xl font-bold mb-3 text-bizai-darkGray dark:text-white">
                      {feature.title}
                    </h3>
                    <p className="text-bizai-mediumGray dark:text-gray-300 leading-relaxed">
                      {feature.description}
                    </p>

                    {/* Animated arrow on hover */}
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      whileHover={{ opacity: 1, x: 0 }}
                      className="absolute bottom-8 right-8"
                    >
                      <ArrowRight className={`w-6 h-6 ${feature.color}`} />
                    </motion.div>
                  </motion.div>
                </FloatingCard>
              ))}
            </div>
          </div>
        </section>

        {/* Tech Stack Showcase - Infinite Scroll */}
        <section className="py-20 relative bg-gradient-to-b from-transparent via-gray-50/50 to-transparent dark:via-gray-900/50 overflow-hidden">
          <div className="container max-w-7xl mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl lg:text-4xl font-bold mb-4 text-bizai-darkGray dark:text-white">
                Built with Modern Technology
              </h2>
              <p className="text-lg text-bizai-mediumGray dark:text-gray-300">
                Enterprise-grade infrastructure for reliability and scale
              </p>
            </motion.div>

            {/* Infinite scrolling logos */}
            <div className="relative">
              {/* Gradient masks for fade effect */}
              <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-white via-white/50 to-transparent dark:from-bizai-primary dark:via-bizai-primary/50 z-10" />
              <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-white via-white/50 to-transparent dark:from-bizai-primary dark:via-bizai-primary/50 z-10" />

              {/* Scrolling container */}
              <div className="flex overflow-hidden">
                <motion.div
                  className="flex gap-12 items-center"
                  animate={{
                    x: [0, -1200],
                  }}
                  transition={{
                    x: {
                      repeat: Infinity,
                      repeatType: "loop",
                      duration: 20,
                      ease: "linear",
                    },
                  }}
                >
                  {/* First set of logos */}
                  {[...techStack, ...techStack].map((tech, index) => (
                    <div
                      key={`first-${index}`}
                      className="flex flex-col items-center justify-center min-w-[120px] group"
                    >
                      <div className="p-4 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 shadow-md group-hover:shadow-lg transition-all duration-300 group-hover:scale-110">
                        <tech.icon className="w-12 h-12 text-bizai-accent1 group-hover:text-bizai-accent2 transition-colors" />
                      </div>
                      <span className="mt-3 text-sm font-medium text-bizai-darkGray dark:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        {tech.name}
                      </span>
                    </div>
                  ))}
                  {/* Second set for seamless loop */}
                  {[...techStack, ...techStack].map((tech, index) => (
                    <div
                      key={`second-${index}`}
                      className="flex flex-col items-center justify-center min-w-[120px] group"
                    >
                      <div className="p-4 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 shadow-md group-hover:shadow-lg transition-all duration-300 group-hover:scale-110">
                        <tech.icon className="w-12 h-12 text-bizai-accent1 group-hover:text-bizai-accent2 transition-colors" />
                      </div>
                      <span className="mt-3 text-sm font-medium text-bizai-darkGray dark:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        {tech.name}
                      </span>
                    </div>
                  ))}
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonials Carousel */}
        <section className="py-20 relative">
          <div className="container max-w-7xl mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl lg:text-4xl font-bold mb-4 text-bizai-darkGray dark:text-white">
                Trusted by Industry Leaders
              </h2>
              <p className="text-lg text-bizai-mediumGray dark:text-gray-300">
                See what our customers have to say
              </p>
            </motion.div>

            <div className="relative max-w-4xl mx-auto">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTestimonial}
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -50 }}
                  transition={{ duration: 0.5 }}
                  className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-8 md:p-12 shadow-xl border border-gray-200/50 dark:border-gray-700/50"
                >
                  <div className="flex gap-1 mb-6">
                    {[...Array(testimonials[activeTestimonial].rating)].map((_, i) => (
                      <Star key={i} className="w-5 h-5 fill-bizai-accent2 text-bizai-accent2" />
                    ))}
                  </div>
                  <blockquote className="text-xl md:text-2xl font-medium text-bizai-darkGray dark:text-white mb-6 leading-relaxed">
                    "{testimonials[activeTestimonial].quote}"
                  </blockquote>
                  <div>
                    <p className="font-semibold text-bizai-darkGray dark:text-white">
                      {testimonials[activeTestimonial].author}
                    </p>
                    <p className="text-bizai-mediumGray dark:text-gray-400">
                      {testimonials[activeTestimonial].role}
                    </p>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Testimonial indicators */}
              <div className="flex justify-center gap-2 mt-6">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveTestimonial(index)}
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      activeTestimonial === index
                        ? 'w-8 bg-bizai-accent1'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Modern CTA Section */}
        <section className="py-20 relative">
          <div className="container max-w-7xl mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="relative rounded-3xl overflow-hidden"
            >
              {/* Animated gradient background */}
              <div className="absolute inset-0 bg-gradient-to-r from-bizai-accent1 via-bizai-accent2 to-bizai-accent1 animate-gradient-shift" />

              <div className="relative z-10 p-12 md:p-20 text-center">
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                  {t('landing', 'ctaTitle')}
                </h2>
                <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto">
                  {t('landing', 'ctaDescription')}
                </p>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-block"
                >
                  <Button
                    size="lg"
                    onClick={() => router.push('/login')}
                    className="bg-white text-bizai-primary hover:bg-gray-100 px-10 py-6 text-lg font-semibold rounded-xl shadow-xl transition-all duration-300"
                  >
                    {t('landing', 'ctaButton')}
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Trusted By Section */}
        <section className="py-16 relative">
          <div className="container max-w-7xl mx-auto px-4">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <p className="text-sm uppercase tracking-wider text-bizai-mediumGray dark:text-gray-400 mb-8">
                Trusted by 500+ companies worldwide
              </p>
              <div className="flex flex-wrap items-center justify-center gap-12">
                {['TechCorp', 'FinanceHub', 'GlobalAudit', 'DataSync', 'CloudVault'].map((company, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    viewport={{ once: true }}
                    className="flex items-center gap-2 opacity-60 dark:opacity-50 grayscale hover:opacity-100 hover:grayscale-0 transition-all duration-300"
                  >
                    <Building className="w-8 h-8 text-bizai-darkGray dark:text-gray-400" />
                    <span className="text-xl font-semibold text-bizai-darkGray dark:text-gray-400">{company}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>
      </main>

      <LandingFooter />

      {/* Demo Video Modal */}
      <AnimatePresence>
        {showDemoModal && (
          <>
            {/* Backdrop with blur */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowDemoModal(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: "spring", damping: 20, stiffness: 300 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
            >
              <div className="relative bg-black rounded-2xl shadow-2xl max-w-5xl w-full overflow-hidden pointer-events-auto">
                {/* Close button */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setShowDemoModal(false)}
                  className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors"
                >
                  <X className="w-6 h-6 text-white" />
                </motion.button>

                {/* Video Container */}
                <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                  <iframe
                    className="absolute inset-0 w-full h-full"
                    src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&rel=0&showinfo=0"
                    title="HappyRobot Demo Video"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <style jsx>{`
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }

        .animate-blob {
          animation: blob 7s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }

        @keyframes gradient-shift {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }

        .animate-gradient-shift {
          background-size: 200% 200%;
          animation: gradient-shift 4s ease infinite;
        }
      `}</style>
    </div>
  );
}
