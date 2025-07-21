import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare, BookOpen, Users, Shield } from "lucide-react";

const Index = () => {
  const features = [
    {
      icon: MessageSquare,
      title: "AI-Powered Chat",
      description: "Engage with theological texts through intelligent conversation"
    },
    {
      icon: BookOpen,
      title: "Vast Library",
      description: "Access thousands of theological documents and historical texts"
    },
    {
      icon: Users,
      title: "Scholarly Community",
      description: "Connect with researchers and theologians worldwide"
    },
    {
      icon: Shield,
      title: "Trusted Sources",
      description: "Curated collection of authoritative theological works"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-primary">Theo</span>
          </div>
          <div className="space-x-4">
            <Link to="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link to="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Your AI-Powered Theological Research Assistant
          </h1>
          <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
            Unlock the depths of theological knowledge with Theo. Our advanced RAG system helps you 
            explore scripture, church history, and systematic theology with unprecedented insight.
          </p>
          <div className="flex justify-center space-x-4">
            <Link to="/chat">
              <Button size="lg" className="px-8">
                <MessageSquare className="mr-2 h-5 w-5" />
                Start Researching
              </Button>
            </Link>
            <Link to="/admin">
              <Button size="lg" variant="outline" className="px-8">
                <Shield className="mr-2 h-5 w-5" />
                Admin Access
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-20">
          {features.map((feature, index) => (
            <Card key={index} className="text-center border-0 shadow-lg bg-card/50 backdrop-blur">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm leading-relaxed">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* CTA Section */}
        <div className="text-center mt-20">
          <Card className="max-w-2xl mx-auto border-0 shadow-xl bg-gradient-to-r from-primary/5 to-secondary/5">
            <CardHeader>
              <CardTitle className="text-2xl">Ready to Begin Your Research?</CardTitle>
              <CardDescription className="text-base">
                Join scholars and students worldwide in exploring theological truth
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/register">
                <Button size="lg" className="w-full max-w-xs">
                  Create Your Account
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Index;
