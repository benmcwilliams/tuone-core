```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Enbridge-Éolien-France-2-S.à.r.l" or company = "Enbridge Éolien France 2 S.à.r.l")
sort location, dt_announce desc
```
