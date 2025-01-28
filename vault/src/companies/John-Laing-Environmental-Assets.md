```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "John-Laing-Environmental-Assets" or company = "John Laing Environmental Assets")
sort location, dt_announce desc
```
