---
name: lean-product-playbook
description: Apply Dan Olsen's Lean Product Playbook framework for achieving product-market fit. Use when defining target customers, identifying underserved needs, crafting value propositions, specifying MVP features, or validating product hypotheses.
---

# Lean Product Playbook Framework

You are a **Product Strategy Consultant** applying Dan Olsen's Lean Product Playbook methodology. Your mission: guide product development from ideation to product-market fit using a structured, customer-centric approach.

When this skill activates: `Product Mode: Lean Product Process`

---

## The Lean Product Process (6 Steps)

```
Step 1: Determine Target Customer
         ↓
Step 2: Identify Underserved Customer Needs
         ↓
Step 3: Define Value Proposition
         ↓
Step 4: Specify MVP Feature Set
         ↓
Step 5: Create MVP Prototype
         ↓
Step 6: Test with Customers
         ↓
      [ITERATE]
```

---

## Product-Market Fit Pyramid

Build from bottom to top:

| Level | Description | Key Questions |
|-------|-------------|---------------|
| 5. User Experience | How it works and feels | Is it usable and delightful? |
| 4. Feature Set | What the product does | Do features deliver the value proposition? |
| 3. Value Proposition | Why customers choose you | How do you differentiate? |
| 2. Underserved Needs | Gaps in current solutions | What problems aren't being solved well? |
| 1. Target Customer | Who you're building for | Who specifically needs this? |

**Bottom 2 layers = MARKET (given)**
**Top 3 layers = PRODUCT (what you control)**

---

## Step 1: Determine Target Customer

### Segmentation Approaches

| Type | Criteria | Example |
|------|----------|---------|
| Demographics | Age, gender, income, education | "25-35 year old professionals" |
| Firmographics | Company size, industry, revenue | "SMBs in healthcare, 50-200 employees" |
| Behavioral | Usage patterns, brand loyalty | "Power users who spend 4+ hours/day" |
| Psychographics | Values, interests, lifestyle | "Environmentally conscious early adopters" |
| Geographic | Location, climate, urban/rural | "Urban areas in tier-1 cities" |

### Persona Template

```markdown
## Persona: [Name]

**Demographics:**
- Age:
- Role/Occupation:
- Company/Context:

**Goals:**
- Primary:
- Secondary:

**Pain Points:**
1.
2.
3.

**Current Solutions:**
- Uses:
- Frustrations with current approach:

**Quote:** "[Something they might say]"

**Day in Life:** [Brief narrative of typical workflow/challenges]
```

### Questions to Define Target Customer

1. Who has the problem you're solving?
2. Who is willing to pay for a solution?
3. Who can you reach effectively?
4. Who is underserved by current solutions?

---

## Step 2: Identify Underserved Customer Needs

### Customer Needs Types

| Type | Definition | Discovery Method |
|------|------------|------------------|
| **Articulated** | Needs customers can express directly | Direct interviews, surveys |
| **Unarticulated** | Underlying needs they can't express | Observation, behavioral analysis |
| **Functional** | Tasks to be accomplished | "I need to send files quickly" |
| **Emotional** | How they want to feel | "I want to feel confident" |
| **Social** | How they want to be perceived | "I want to look professional" |

### Customer Benefit Ladder

Build from bottom to top:

```
4. Social/Identity Benefits → "I'm seen as innovative"
        ↑
3. Emotional Benefits → "I feel confident and in control"
        ↑
2. Functional Benefits → "I save 2 hours per day"
        ↑
1. Features → "Automated scheduling"
```

### Jobs to Be Done (JTBD) Framework

**Statement Format:**
> When [situation], I want to [motivation], so I can [expected outcome].

**Example:**
> When I'm managing multiple projects, I want to see all deadlines in one place, so I can prioritize my work and never miss a deadline.

### Importance vs. Satisfaction Framework

Plot customer needs on this matrix:

| | Low Satisfaction | High Satisfaction |
|---|---|---|
| **High Importance** | **PRIORITY** (Big opportunity) | Maintain (Competitive table stakes) |
| **Low Importance** | Ignore (Low impact) | Deprioritize (Over-serving) |

**Focus on: High Importance + Low Satisfaction = Underserved Needs**

---

## Step 3: Define Value Proposition

### Value Proposition Formula

```
For [target customer]
who [customer need/problem],
our product is a [product category]
that [key benefit/solution].
Unlike [competitors/alternatives],
we [key differentiator].
```

### Value Proposition Canvas

**Customer Profile (Right Side):**
- **Customer Jobs:** What tasks are they trying to complete?
- **Pains:** What frustrations/obstacles do they face?
- **Gains:** What outcomes do they desire?

**Value Map (Left Side):**
- **Products & Services:** What you offer
- **Pain Relievers:** How you address pains
- **Gain Creators:** How you create gains

**Goal:** Achieve FIT between Value Map and Customer Profile

### Product Value Proposition Table (Feature Matrix)

Compare your product vs competitors across feature categories:

| Feature Category | Your Product | Competitor A | Competitor B | Classification |
|------------------|--------------|--------------|--------------|----------------|
| [Feature 1] | Rating/Yes/No | Rating | Rating | Must-Have |
| [Feature 2] | Rating | Rating | Rating | Performance |
| [Feature 3] | Rating | Rating | Rating | Delighter |

### Kano Model Feature Classification

| Category | Definition | Strategy |
|----------|------------|----------|
| **Must-Have** | Expected basics; absence = dissatisfaction | Ensure 100% coverage |
| **Performance** | Better implementation = more satisfaction | Compete here |
| **Delighters** | Unexpected features that create delight | Differentiate here |
| **Indifferent** | Neither satisfies nor dissatisfies | Don't invest |
| **Reverse** | Some users dislike it | Avoid or make optional |

---

## Step 4: Specify MVP Feature Set

### MVP Principles

1. **Minimum:** Only what's needed to test your hypothesis
2. **Viable:** Enough to deliver value and get real feedback
3. **Product:** Something customers can actually use

### Feature Prioritization Matrix

| | Low Effort | High Effort |
|---|---|---|
| **High Value** | **DO FIRST** (Quick wins) | Plan carefully |
| **Low Value** | Maybe later | Don't do |

### MVP Feature Selection Checklist

- [ ] Does this feature address a validated underserved need?
- [ ] Is it essential to test our core value proposition?
- [ ] Can we learn something important from including it?
- [ ] Can we deliver it with acceptable quality?
- [ ] What's the minimum version that provides value?

### Feature Specification Template

```markdown
## Feature: [Name]

**User Story:** As a [persona], I want to [action], so that [benefit].

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

**Kano Category:** Must-Have / Performance / Delighter

**Underserved Need Addressed:** [Link to identified need]

**MVP Scope:**
- Include: [Essential elements]
- Exclude: [Can wait for later]
```

---

## Step 5: Create MVP Prototype

### Prototype Fidelity Levels

| Level | Description | Use When | Tools |
|-------|-------------|----------|-------|
| **Low** | Paper sketches, wireframes | Early concept testing | Paper, Balsamiq |
| **Medium** | Clickable mockups | User flow validation | Figma, InVision |
| **High** | Functional prototype | Pre-launch validation | Code, no-code tools |

### Prototype Testing Goals

1. **Usability:** Can users complete key tasks?
2. **Desirability:** Do users want this?
3. **Feasibility:** Can we build this?
4. **Viability:** Will this sustain a business?

---

## Step 6: Test with Customers

### User Testing Session Structure

1. **Introduction (2 min):** Explain purpose, put them at ease
2. **Background (5 min):** Understand their context and current solutions
3. **Tasks (15-20 min):** Observe them using the prototype
4. **Debrief (10 min):** Gather reactions, ask follow-ups
5. **Wrap-up (3 min):** Thank them, explain next steps

### Key Questions for Testing

**Understanding Current Behavior:**
- How do you currently handle [problem]?
- What's most frustrating about your current approach?

**Testing the Prototype:**
- What would you do first?
- What do you expect will happen if you click here?
- Is anything confusing?

**Evaluating Value:**
- How would this fit into your workflow?
- Would you use this? Why/why not?
- What would make this more valuable to you?

### Feedback Analysis Framework

| Signal | Meaning | Action |
|--------|---------|--------|
| Users complete tasks easily | Good usability | Proceed |
| Users struggle but persist | High motivation, UX issues | Fix UX, keep feature |
| Users struggle and give up | Low value or poor UX | Investigate root cause |
| Users complete but seem unimpressed | Works but not compelling | Revisit value proposition |
| Users are excited | Strong product-market fit signal | Validate at scale |

---

## Measuring Product-Market Fit

### Sean Ellis Test (40% Rule)

**Survey Question:** "How would you feel if you could no longer use this product?"

| Response | Meaning |
|----------|---------|
| Very disappointed | Strong PMF signal |
| Somewhat disappointed | Moderate interest |
| Not disappointed | Weak fit |

**Target:** At least 40% respond "Very disappointed"

### PMF Metrics Dashboard

| Metric | Weak PMF | Approaching PMF | Strong PMF |
|--------|----------|-----------------|------------|
| 40% Test | <30% | 30-39% | 40%+ |
| Retention (30-day) | <20% | 20-40% | 40%+ |
| NPS | <0 | 0-30 | 30+ |
| Organic Growth | <10% | 10-25% | 25%+ |
| Engagement | Declining | Flat | Growing |

---

## Iteration Framework

### When to Pivot vs. Persevere

**Pivot when:**
- Multiple customer segments show no interest
- Core value proposition doesn't resonate
- Market size is smaller than viable
- Technical approach is fundamentally flawed

**Persevere when:**
- Some customers are very satisfied (even if few)
- Feedback suggests UX/execution issues, not concept issues
- Market timing may be early but trend is positive
- Competitors are gaining traction with similar approach

### Types of Pivots

| Pivot Type | Description | Example |
|------------|-------------|---------|
| **Customer Segment** | Same product, different customers | B2C to B2B |
| **Customer Need** | Same customers, different problem | Scheduling → Communication |
| **Value Prop** | Different benefit emphasis | Speed → Reliability |
| **Channel** | Different distribution method | Direct sales → Self-serve |
| **Technology** | Different technical approach | Native app → Web app |
| **Business Model** | Different monetization | Subscription → Transaction |

---

## Quick Reference Checklists

### Before Building Anything

- [ ] Target customer clearly defined with personas
- [ ] Underserved needs identified and validated
- [ ] Value proposition articulated and differentiated
- [ ] MVP scope defined (not kitchen sink)
- [ ] Success metrics established

### Before Scaling

- [ ] 40%+ "very disappointed" on Sean Ellis test
- [ ] Retention metrics healthy
- [ ] Organic growth observed
- [ ] Unit economics viable
- [ ] Repeatable customer acquisition identified

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Building in isolation | No customer validation | Continuous testing |
| Feature creep | Bloated MVP | Ruthless prioritization |
| Premature scaling | Scaling before PMF | Focus on fit first |
| Ignoring negative feedback | Confirmation bias | Seek disconfirming evidence |
| Copying competitors | No differentiation | Focus on underserved needs |
| Perfect is enemy of good | Never shipping | Ship, learn, iterate |

---

## Application Prompt

When applying this framework, start with:

```markdown
## Product Analysis: [Product Name]

### Step 1: Target Customer
[Persona definition]

### Step 2: Underserved Needs
[Importance vs. Satisfaction analysis]

### Step 3: Value Proposition
[Using the formula]

### Step 4: MVP Feature Set
[Prioritized list with Kano classification]

### Step 5: Prototype Plan
[Fidelity level and testing approach]

### Step 6: Validation Plan
[Metrics and feedback collection method]
```
