```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "I&H-Brown" or company = "I&H Brown")
sort location, dt_announce desc
```
