// @vitest-environment jsdom
import React from 'react';
import { afterEach,describe,it,expect } from 'vitest';
import { cleanup,render,screen,fireEvent,within } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { ActionCard } from '../../src/components/ActionCard';
import { SelfCare } from '../../src/components/SelfCare';
import copy from '../../src/data/ui-copy.json';
import type { Cards } from '../../src/data/load';
const cards:Cards=JSON.parse(readFileSync(resolve(import.meta.dirname,'../../public/demo/cards.json'),'utf8'));
afterEach(cleanup);

describe('source-owned self-care guidance',()=>{
 it('covers all seven card ids',()=>{expect(Object.keys(copy.self_care.cards).sort()).toEqual(cards.cards.map(c=>c.id).sort());expect(cards.cards).toHaveLength(7);});
 for(const card of cards.cards)it(`renders after ${card.id}, opens initially and keeps its disclaimer while collapsed`,()=>{
  const page=render(<ActionCard card={card} onAction={()=>{}}/>);
  const action=screen.getByRole('article',{name:card.heading});
  const box=screen.getByRole('region',{name:copy.self_care.heading});
  expect(action.nextElementSibling).toBe(box);
  const button=within(box).getByRole('button',{name:copy.self_care.heading});
  const data=Object.entries(copy.self_care.cards).find(([id])=>id===card.id)![1];
  expect(button.getAttribute('aria-expanded')).toBe('true');
  expect(within(box).getAllByRole('listitem').map(e=>e.textContent)).toEqual(data.steps);
  expect(within(box).getByText(data.sources)).toBeTruthy();
  expect(box.textContent).not.toMatch(/\bmg\b|tablet|medication|diagnos/i);
  if(!card.id.startsWith('radiation-'))expect(box.textContent).not.toMatch(/dose/i);
  expect(within(box).getByText(copy.self_care.disclaimer).closest('[hidden]')).toBeNull();
  fireEvent.click(button);
  expect(button.getAttribute('aria-expanded')).toBe('false');expect(within(box).queryByRole('list')).toBeNull();
  expect(within(box).getByText(copy.self_care.disclaimer).closest('[hidden]')).toBeNull();
  expect(within(box).getByRole('button',{name:copy.self_care.heading})).toBeTruthy();
  fireEvent.click(button);expect(within(box).getAllByRole('listitem')).toHaveLength(data.steps.length);
  expect(action.nextElementSibling).toBe(box);expect(page.container.querySelectorAll('.action-card')).toHaveLength(1);
 });
 it('does not render an empty box for an unknown id',()=>{
  const view=render(<SelfCare cardId="unknown-card"/>);expect(view.container.innerHTML).toBe('');
  view.rerender(<SelfCare cardId="__proto__"/>);expect(view.container.innerHTML).toBe('');
 });
 it('keeps urgent card content and action controls ahead of general guidance',()=>{
  const urgent=cards.cards.find(c=>c.id==='radiation-spe-procedure')!;
  render(<ActionCard card={urgent} onAction={()=>{}}/>);
  const card=screen.getByRole('article',{name:urgent.heading}),box=screen.getByRole('region',{name:copy.self_care.heading});
  expect(within(card).getByRole('button',{name:'Contact onboard CMO'})).toBeTruthy();
  expect(card.compareDocumentPosition(box)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(card.contains(box)).toBe(false);expect(box.classList.contains('status-act')).toBe(false);
 });
});
