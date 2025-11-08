"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { MessageSquare, Send, Shield, Clock, Users, Receipt, Settings, Mic, CodeIcon, Brush, Brain, Code, ChevronRight, ChevronLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Screenshot {
  src: string;
  caption: string;
}

export default function SeeItInAction() {
  const [showVideo, setShowVideo] = useState(false);

  const screenshots: Screenshot[] = [
    { src: "/images/whatsapp4.jpg", caption: "Pay friends & family" },
    { src: "/images/whatsapp5.jpg", caption: "Sender's conversation view" },
    { src: "/images/whatsapp6.jpg", caption: "Recipient's notification" },
  ];

  const videoDemo = "/videos/demo.mp4";

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-black/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-semibold">ArcAgent</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm text-gray-400 hover:text-white transition">
              Features
            </Link>
            <Link href="#how-it-works" className="text-sm text-gray-400 hover:text-white transition">
              How It Works
            </Link>
            <Link href="#team" className="text-sm text-gray-400 hover:text-white transition">
              Team
            </Link>
            <Link href="#faq" className="text-sm text-gray-400 hover:text-white transition">
              FAQ
            </Link>
          </div>
          <a
            href="https://github.com/andyanalog/arc-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-white text-black rounded-lg text-sm font-medium hover:bg-gray-100 transition flex items-center gap-2"
          >
            <CodeIcon className="w-5 h-5" />
            GitHub Repository
          </a>

        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/20 bg-purple-500/10 text-purple-400 text-sm mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
            </span>
            Powered by Arc & Circle
          </div>
          
          <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-6 bg-linear-to-b from-white to-gray-500 bg-clip-text text-transparent">
            Chat. Command. Pay.
          </h1>
          
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12">
            The conversational AI financial assistant that lives inside WhatsApp. 
            Send USDC payments naturally, without switching apps.
          </p>

          <div className="flex items-center justify-center gap-4">
            <a
                  href="https://lablab.ai/event/ai-agents-arc-usdc/kel?channelId=1432495900198174840"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-8 py-4 bg-white text-black rounded-lg font-medium hover:bg-gray-100 transition inline-flex items-center gap-2"
                >
                  Request a Demo
                </a>
          </div>

          {/* Animated gradient orbs */}
          <div className="absolute top-40 left-20 w-72 h-72 bg-purple-500/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-60 right-20 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-sm font-semibold text-purple-400 mb-2 uppercase tracking-wider">
              FEATURES
            </h2>
            <p className="text-4xl md:text-5xl font-bold">
              Everything you need
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { 
                title: "Conversational Payments", 
                desc: "Send money by chatting naturally",
                icon: MessageSquare,
                gradient: "from-purple-500 to-pink-500"
              },
              { 
                title: "Multi-Layer Security", 
                desc: "PIN protection & encrypted storage",
                icon: Shield,
                gradient: "from-pink-500 to-purple-500"
              },
              { 
                title: "Instant Transfers", 
                desc: "Real-time USDC payments on Arc",
                icon: Send,
                gradient: "from-purple-500 to-blue-500"
              },
              { 
                title: "Split Payments", 
                desc: "Share bills with friends easily",
                icon: Users,
                gradient: "from-blue-500 to-purple-500"
              },
              { 
                title: "Auto Receipts", 
                desc: "Transaction history & confirmations",
                icon: Receipt,
                gradient: "from-purple-500 to-pink-500"
              },
              { 
                title: "Voice Payments", 
                desc: "Optional voice commands with Eleven Labs",
                icon: Mic,
                gradient: "from-pink-500 to-purple-500"
              }
            ].map((feature) => (
              <div key={feature.title} className="group relative">
                <div className="absolute inset-0 bg-linear-to-br from-purple-500/10 to-pink-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition" />
                <div className="relative p-6 border border-white/10 rounded-2xl bg-black hover:border-purple-500/50 transition h-full">
                  <div className={`w-12 h-12 rounded-xl bg-linear-to-br ${feature.gradient} flex items-center justify-center mb-4`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-400 text-sm">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-sm font-semibold text-purple-400 mb-2 uppercase tracking-wider">
              HOW IT WORKS
            </h2>
            <p className="text-4xl md:text-5xl font-bold">
              4 steps to get started
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { num: "01", title: "Register", desc: "Send 'Hi' to start registration", icon: MessageSquare },
              { num: "02", title: "Verify", desc: "Enter verification code", icon: Shield },
              { num: "03", title: "Setup PIN", desc: "Secure your wallet", icon: Settings },
              { num: "04", title: "Start Paying", desc: "Send money instantly", icon: Send }
            ].map((step) => (
              <div key={step.num} className="relative group">
                <div className="absolute inset-0 bg-linear-to-br from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition opacity-0 group-hover:opacity-100" />
                <div className="relative p-8 border border-white/10 rounded-2xl bg-black hover:border-purple-500/50 transition">
                  <step.icon className="w-8 h-8 text-purple-400 mb-4" />
                  <div className="text-5xl font-bold text-white/18 mb-2">{step.num}</div>
                  <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                  <p className="text-gray-400 text-sm">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Screenshots Section */}
      <section className="py-20 px-6 overflow-hidden">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-sm font-semibold text-purple-400 mb-2 uppercase tracking-wider">
            SEE IT IN ACTION
          </h2>
          <p className="text-4xl md:text-5xl font-bold">Chat-based payments</p>
        </div>

        <div className="relative flex justify-center">
          <AnimatePresence mode="wait">
            {!showVideo ? (
              <motion.div
                key="images"
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 50 }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
                className="grid md:grid-cols-3 gap-6"
              >
                {screenshots.map((item) => (
                  <div key={item.caption} className="relative group">
                    <div className="absolute inset-0 bg-linear-to-br from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition" />
                    <div className="relative border border-white/10 rounded-2xl bg-linear-to-b from-white/5 to-black p-4 hover:border-purple-500/50 transition">
                      <Image
                        src={item.src}
                        alt={item.caption}
                        width={400}
                        height={800}
                        className="rounded-xl border border-white/10 object-cover w-full h-auto"
                      />
                      <p className="text-center mt-4 text-sm text-gray-400">
                        {item.caption}
                      </p>
                    </div>
                  </div>
                ))}
              </motion.div>
            ) : (
              <motion.div
                key="video"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
                className="grid md:grid-cols-3 gap-6"
              >
                <div className="hidden md:block" />

                <div className="relative group">
                  <div className="absolute inset-0 bg-linear-to-br from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition" />
                  <div className="relative border border-white/10 rounded-2xl bg-linear-to-b from-white/5 to-black p-4 hover:border-purple-500/50 transition">
                    <video
                      src={videoDemo}
                      controls
                      autoPlay
                      playsInline
                      loop
                      className="rounded-xl border border-white/10 object-cover w-full h-auto"
                    />
                    <p className="text-center mt-4 text-sm text-gray-400">
                      Product demo in action
                    </p>
                  </div>
                </div>

                <div className="hidden md:block" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Left Arrow (shows only when video is active) */}
          {showVideo && (
            <button
              onClick={() => setShowVideo(false)}
              className="absolute left-0 top-1/2 -translate-y-1/2 bg-purple-500 hover:bg-purple-600 text-white rounded-full p-3 shadow-lg transition"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
          )}

          {/* Right Arrow (shows only when screenshots are visible) */}
          {!showVideo && (
            <button
              onClick={() => setShowVideo(true)}
              className="absolute right-0 top-1/2 -translate-y-1/2 bg-purple-500 hover:bg-purple-600 text-white rounded-full p-3 shadow-lg transition"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          )}
        </div>
      </div>
    </section>

      {/* Team Section */}
      <section id="team" className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-sm font-semibold text-purple-400 mb-2 uppercase tracking-wider">
            TEAM
          </h2>
          <p className="text-4xl md:text-5xl font-bold">
            Built by innovators
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {[
            {
              name: "Kikosem Igwubor",
              role: "Backend & Workflows",
              icon: <Code className="w-12 h-12 text-purple-400 group-hover:text-purple-300 transition" />,
            },
            {
              name: "Emmanuel Raymond",
              role: "UX & Interface",
              icon: <Brush className="w-12 h-12 text-pink-400 group-hover:text-pink-300 transition" />,
            },
            {
              name: "Andres Lozano",
              role: "Software Dev / AI Integration",
              icon: <Brain className="w-12 h-12 text-blue-400 group-hover:text-blue-300 transition" />,
            },
          ].map((member) => (
            <div key={member.name} className="relative group">
              <div className="absolute inset-0 bg-linear-to-br from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition" />
              <div className="relative p-6 border border-white/10 rounded-2xl bg-black hover:border-purple-500/50 transition text-center">
                <div className="flex justify-center mb-4">{member.icon}</div>
                <h3 className="text-lg font-semibold mb-1">{member.name}</h3>
                <p className="text-gray-400 text-sm">{member.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-sm font-semibold text-purple-400 mb-2 uppercase tracking-wider">
              FREQUENTLY ASKED QUESTIONS
            </h2>
          </div>

          <div className="space-y-4">
            {[
              { q: "What is ArcAgent?", a: "ArcAgent is an AI-powered payment assistant that lets you send USDC via WhatsApp using natural language." },
              { q: "How does ArcAgent stay secure?", a: "We use PIN protection, encrypted storage, and secure Circle wallet infrastructure." },
              { q: "Where do I get started?", a: "Simply message the ArcAgent WhatsApp number with 'Hi' to begin registration." },
              { q: "How do I get started?", a: "Send 'Hi' to our WhatsApp number to start registration." },
              { q: "Can I try this on Arc mainnet?", a: "Currently we support Arc testnet. Mainnet support coming soon." }
            ].map((item, i) => (
              <details key={i} className="group border border-white/10 rounded-xl bg-black hover:border-purple-500/50 transition">
                <summary className="p-6 cursor-pointer list-none flex items-center justify-between">
                  <span className="font-medium">{item.q}</span>
                  <span className="text-gray-400 group-open:rotate-180 transition-transform">↓</span>
                </summary>
                <div className="px-6 pb-6 text-gray-400 text-sm border-t border-white/5 pt-4">
                  {item.a}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="relative">
            <div className="absolute inset-0 bg-linear-to-br from-purple-500/20 to-pink-500/20 rounded-3xl blur-3xl" />
            <div className="relative border border-white/10 rounded-3xl bg-black p-12">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                Ready to get started?
              </h2>
              <p className="text-xl text-gray-400 mb-8">
                Join the future of conversational payments
              </p>
                <a
                  href="https://lablab.ai/event/ai-agents-arc-usdc/kel?channelId=1432495900198174840"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-8 py-4 bg-white text-black rounded-lg font-medium hover:bg-gray-100 transition inline-flex items-center gap-2"
                >
                  Request a Demo
                </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <span className="text-xl font-semibold">ArcAgent</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-400">
              <Link href="/privacy" className="hover:text-white transition">Privacy Policy</Link>
              <Link href="/terms" className="hover:text-white transition">Terms of Service</Link>
              <Link href="/docs" className="hover:text-white transition">Documentation</Link>
            </div>
            <p className="text-sm text-gray-400">
              © 2025 ArcAgent. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}