```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Google-Inc." or company = "Google Inc.")
sort location, dt_announce desc
```
