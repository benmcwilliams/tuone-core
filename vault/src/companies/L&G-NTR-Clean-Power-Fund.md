```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "L&G NTR Clean Power Fund"
sort location, dt_announce desc
```
