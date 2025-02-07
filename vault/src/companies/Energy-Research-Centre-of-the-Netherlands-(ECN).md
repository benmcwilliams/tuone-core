```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energy-Research-Centre-of-the-Netherlands-(ECN)" or company = "Energy Research Centre of the Netherlands (ECN)")
sort location, dt_announce desc
```
