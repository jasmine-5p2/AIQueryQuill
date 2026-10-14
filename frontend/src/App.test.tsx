import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
describe('QueryQuill app',()=>{it('shows the sign-in screen when signed out',()=>{localStorage.clear();render(<App/>);expect(screen.getByText('Welcome back')).toBeTruthy();expect(screen.getByLabelText('Username')).toBeTruthy()})});
