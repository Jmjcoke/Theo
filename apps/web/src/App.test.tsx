import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the Welcome to Theo heading', () => {
    render(<App />);
    expect(screen.getByText('Welcome to Theo.')).toBeInTheDocument();
  });

  it('renders the theological research assistant subtitle', () => {
    render(<App />);
    expect(screen.getByText('Your AI-Powered Theological Research Assistant')).toBeInTheDocument();
  });

  it('renders navigation buttons', () => {
    render(<App />);
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Get Started')).toBeInTheDocument();
  });

  it('renders feature cards', () => {
    render(<App />);
    expect(screen.getByText('AI-Powered Chat')).toBeInTheDocument();
    expect(screen.getByText('Vast Library')).toBeInTheDocument();
    expect(screen.getByText('Scholarly Community')).toBeInTheDocument();
    expect(screen.getByText('Trusted Sources')).toBeInTheDocument();
  });
});