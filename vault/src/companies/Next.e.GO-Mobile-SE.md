```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Next.e.GO-Mobile-SE" or company = "Next.e.GO Mobile SE")
sort location, dt_announce desc
```
