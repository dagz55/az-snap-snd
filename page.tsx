"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/use-toast"
import { getSubscriptions, getSnapshotSummary, getRecentActivity, createSnapshot, deleteOldSnapshots, searchSnapshots, getFilteredChartData, toggleFavoriteSnapshot, getFavoriteSnapshots, Subscription, SnapshotSummary, Activity, SnapshotSearchResult } from "@/services/api"
import { useAuth } from "@/contexts/AuthContext"
import { BarChart, LineChart, PieChart } from "@/components/ui/chart"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Loader2, Plus, Trash2, Search, Star, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { DatePickerWithRange } from "@/components/ui/date-range-picker"
import { addDays } from "date-fns"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

export function Dashboard() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [selectedSubscription, setSelectedSubscription] = useState<string>("")
  const [summary, setSummary] = useState<SnapshotSummary | null>(null)
  const [recentActivity, setRecentActivity] = useState<Activity[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<SnapshotSearchResult[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [resourceGroupName, setResourceGroupName] = useState("")
  const [diskName, setDiskName] = useState("")
  const [deleteOlderThanDays, setDeleteOlderThanDays] = useState(30)
  const [dateRange, setDateRange] = useState({ from: addDays(new Date(), -30), to: new Date() })
  const [favoriteSnapshots, setFavoriteSnapshots] = useState<SnapshotSearchResult[]>([])
  const { toast } = useToast()
  const { isAuthenticated } = useAuth()
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (isAuthenticated) {
      fetchSubscriptions()
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (selectedSubscription) {
      fetchSnapshotSummary()
      fetchRecentActivity()
      fetchFavoriteSnapshots()
      connectWebSocket()
    }

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [selectedSubscription])

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8080')

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      if (ws.current) {
        ws.current.send(JSON.stringify({ type: 'subscribe', subscriptionId: selectedSubscription }))
      }
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'dashboardUpdate') {
        setSummary(data.data.summary)
        setRecentActivity(data.data.recentActivity)
      }
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      toast({
        title: "Error",
        description: "Failed to connect to real-time updates. Please refresh the page.",
        variant: "destructive",
      })
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
    }
  }

  const fetchSubscriptions = async () => {
    try {
      const fetchedSubscriptions = await getSubscriptions()
      setSubscriptions(fetchedSubscriptions)
      if (fetchedSubscriptions.length > 0) {
        setSelectedSubscription(fetchedSubscriptions[0].id)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch subscriptions. Please try again.",
        variant: "destructive",
      })
    }
  }

  const fetchSnapshotSummary = async () => {
    setIsLoading(true)
    try {
      const summaryData = await getSnapshotSummary(selectedSubscription)
      setSummary(summaryData)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch snapshot summary. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchRecentActivity = async () => {
    try {
      const activityData = await getRecentActivity(selectedSubscription)
      setRecentActivity(activityData)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch recent activity. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleCreateSnapshot = async () => {
    try {
      await createSnapshot(selectedSubscription, resourceGroupName, diskName)
      toast({
        title: "Success",
        description: "Snapshot created successfully.",
      })
      setIsCreateDialogOpen(false)
      fetchSnapshotSummary()
      fetchRecentActivity()
    } catch (error) {
      // Error is already handled in the API function
    }
  }

  const handleDeleteOldSnapshots = async () => {
    try {
      const result = await deleteOldSnapshots(selectedSubscription, deleteOlderThanDays)
      toast({
        title: "Success",
        description: `Deleted ${result.deleted.length} old snapshots. ${result.failed.length} failed.`,
      })
      setIsDeleteDialogOpen(false)
      fetchSnapshotSummary()
      fetchRecentActivity()
    } catch (error) {
      // Error is already handled in the API function
    }
  }

  const handleSearch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim() === "") return

    try {
      const results = await searchSnapshots(searchQuery, selectedSubscription)
      setSearchResults(results)
    } catch (error) {
      // Error is already handled in the API function
    }
  }, [searchQuery, selectedSubscription])

  const handleFilterChartData = useCallback(async () => {
    if (!dateRange.from || !dateRange.to) return

    try {
      const filteredData = await getFilteredChartData(
        selectedSubscription,
        dateRange.from.toISOString(),
        dateRange.to.toISOString()
      )
      setSummary(filteredData)
    } catch (error) {
      // Error is already handled in the API function
    }
  }, [selectedSubscription, dateRange])

  const handleToggleFavorite = async (snapshotId: string) => {
    try {
      const { isFavorite } = await toggleFavoriteSnapshot(snapshotId)
      toast({
        title: "Success",
        description: `Snapshot ${isFavorite ? 'added to' : 'removed from'} favorites.`,
      })
      fetchFavoriteSnapshots()
    } catch (error) {
      // Error is already handled in the API function
    }
  }

  const fetchFavoriteSnapshots = async () => {
    try {
      const favorites = await getFavoriteSnapshots(selectedSubscription)
      setFavoriteSnapshots(favorites)
    } catch (error) {
      // Error is already handled in the API function
    }
  }

  const ageDistributionData = summary ? Object.entries(summary.ageDistribution).map(([key, value]) => ({
    name: key,
    value: value
  })) : []

  const statusDistributionData = summary ? Object.entries(summary.statusDistribution).map(([key, value]) => ({
    name: key,
    value: value
  })) : []

  const sizeDistributionData = summary ? [
    { name: "0-1 GB", value: summary.sizeDistribution["0-1"] || 0 },
    { name: "1-10 GB", value: summary.sizeDistribution["1-10"] || 0 },
    { name: "10-100 GB", value: summary.sizeDistribution["10-100"] || 0 },
    { name: "100+ GB", value: summary.sizeDistribution["100+"] || 0 },
  ] : []

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Azure Snapshot Manager Dashboard</CardTitle>
          <CardDescription>Overview of your Azure snapshots across subscriptions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <Select value={selectedSubscription} onValueChange={setSelectedSubscription}>
                <SelectTrigger className="w-[300px]">
                  <SelectValue placeholder="Select a subscription" />
                </SelectTrigger>
                <SelectContent>
                  {subscriptions.map((sub) => (
                    <SelectItem key={sub.id} value={sub.id}>
                      
                      {sub.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <form onSubmit={handleSearch} className="flex-1">
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search snapshots"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-8"
                  />
                </div>
              </form>
            </div>
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : summary ? (
              <>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Snapshots</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{summary.totalCount}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Size</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{summary.totalSizeGB.toFixed(2)} GB</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex space-x-2">
                        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                          <DialogTrigger asChild>
                            <Button size="sm">
                              <Plus className="mr-2 h-4 w-4" /> Create Snapshot
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Create New Snapshot</DialogTitle>
                              <DialogDescription>
                                Enter the details for the new snapshot.
                              </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                              <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="resourceGroup" className="text-right">
                                  Resource Group
                                </Label>
                                <Input
                                  id="resourceGroup"
                                  value={resourceGroupName}
                                  onChange={(e) => setResourceGroupName(e.target.value)}
                                  className="col-span-3"
                                />
                              </div>
                              <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="diskName" className="text-right">
                                  Disk Name
                                </Label>
                                <Input
                                  id="diskName"
                                  value={diskName}
                                  onChange={(e) => setDiskName(e.target.value)}
                                  className="col-span-3"
                                />
                              </div>
                            </div>
                            <DialogFooter>
                              <Button onClick={handleCreateSnapshot}>Create Snapshot</Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                          <DialogTrigger asChild>
                            <Button size="sm" variant="destructive">
                              <Trash2 className="mr-2 h-4 w-4" /> Delete Old
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Delete Old Snapshots</DialogTitle>
                              <DialogDescription>
                                Specify the age of snapshots to delete.
                              </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                              <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="olderThan" className="text-right">
                                  Older than (days)
                                </Label>
                                <Input
                                  id="olderThan"
                                  type="number"
                                  value={deleteOlderThanDays}
                                  onChange={(e) => setDeleteOlderThanDays(parseInt(e.target.value))}
                                  className="col-span-3"
                                />
                              </div>
                            </div>
                            <DialogFooter>
                              <Button onClick={handleDeleteOldSnapshots} variant="destructive">Delete Old Snapshots</Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[100px]">
                        {recentActivity.map((activity, index) => (
                          <div key={index} className="mb-2 text-sm">
                            {activity.action} - {activity.timestamp}
                          </div>
                        ))}
                      </ScrollArea>
                    </CardContent>
                  </Card>
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Age Distribution</CardTitle>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" size="icon">
                            <Calendar className="h-4 w-4" />
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="end">
                          <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                          <div className="p-2">
                            <Button onClick={handleFilterChartData} className="w-full">Apply Filter</Button>
                          </div>
                        </PopoverContent>
                      </Popover>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                      <ChartContainer
                        config={{
                          value: {
                            label: "Count",
                            color: "hsl(var(--chart-1))",
                          },
                        }}
                      >
                        <BarChart
                          data={ageDistributionData}
                          xAxis={[{ scaleType: "band", dataKey: "name" }]}
                          series={[{ dataKey: "value", label: "Count" }]}
                          height={300}
                        >
                          <ChartTooltip
                            content={({ payload, active }) => {
                              if (active && payload && payload.length) {
                                return (
                                  <div className="bg-background p-2 rounded shadow">
                                    <p className="font-bold">{payload[0].payload.name}</p>
                                    <p>Count: {payload[0].value}</p>
                                  </div>
                                )
                              }
                              return null
                            }}
                          />
                        </BarChart>
                      </ChartContainer>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Status Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                      <ChartContainer
                        config={{
                          value: {
                            label: "Count",
                            color: "hsl(var(--chart-2))",
                          },
                        }}
                      >
                        <LineChart
                          data={statusDistributionData}
                          xAxis={[{ scaleType: "point", dataKey: "name" }]}
                          series={[{ dataKey: "value", label: "Count" }]}
                          height={300}
                        >
                          <ChartTooltip
                            content={({ payload, active }) => {
                              if (active && payload && payload.length) {
                                return (
                                  <div className="bg-background p-2 rounded shadow">
                                    <p className="font-bold">{payload[0].payload.name}</p>
                                    <p>Count: {payload[0].value}</p>
                                  </div>
                                )
                              }
                              return null
                            }}
                          />
                        </LineChart>
                      </ChartContainer>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Size Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                      <ChartContainer
                        config={{
                          value: {
                            label: "Count",
                            color: "hsl(var(--chart-3))",
                          },
                        }}
                      >
                        <PieChart
                          data={sizeDistributionData}
                          series={[{ dataKey: "value", label: "Count" }]}
                          height={300}
                        >
                          <ChartTooltip
                            content={({ payload, active }) => {
                              if (active && payload && payload.length) {
                                return (
                                  <div className="bg-background p-2 rounded shadow">
                                    <p className="font-bold">{payload[0].payload.name}</p>
                                    <p>Count: {payload[0].value}</p>
                                  </div>
                                )
                              }
                              return null
                            }}
                          />
                        </PieChart>
                      </ChartContainer>
                    </CardContent>
                  </Card>
                </div>
                <Card>
                  <CardHeader>
                    <CardTitle>Favorite Snapshots</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Resource Group</TableHead>
                          <TableHead>Time Created</TableHead>
                          <TableHead>Size (GB)</TableHead>
                          <TableHead>Action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {favoriteSnapshots.map((snapshot) => (
                          <TableRow key={snapshot.id}>
                            <TableCell>{snapshot.name}</TableCell>
                            <TableCell>{snapshot.resourceGroup}</TableCell>
                            <TableCell>{new Date(snapshot.timeCreated).toLocaleString()}</TableCell>
                            <TableCell>{snapshot.sizeGB}</TableCell>
                            <TableCell>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleToggleFavorite(snapshot.id)}
                              >
                                <Star className="h-4 w-4 fill-current" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </>
            ) : null}
            {searchResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Search Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Resource Group</TableHead>
                        <TableHead>Time Created</TableHead>
                        <TableHead>Size (GB)</TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {searchResults.map((snapshot) => (
                        <TableRow key={snapshot.id}>
                          <TableCell>{snapshot.name}</TableCell>
                          <TableCell>{snapshot.resourceGroup}</TableCell>
                          <TableCell>{new Date(snapshot.timeCreated).toLocaleString()}</TableCell>
                          <TableCell>{snapshot.sizeGB}</TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleToggleFavorite(snapshot.id)}
                            >
                              <Star className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
