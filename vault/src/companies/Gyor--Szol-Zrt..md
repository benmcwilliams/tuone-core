```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Gyor--Szol-Zrt." or company = "Gyor  Szol Zrt.")
sort location, dt_announce desc
```
