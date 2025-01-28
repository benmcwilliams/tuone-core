```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Green-Lighthouse-Développement" or company = "Green Lighthouse Développement")
sort location, dt_announce desc
```
