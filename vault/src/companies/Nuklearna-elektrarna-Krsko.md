```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Nuklearna-elektrarna-Krsko" or company = "Nuklearna elektrarna Krsko")
sort location, dt_announce desc
```
