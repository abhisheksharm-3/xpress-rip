<script lang="ts">
  import { Loader2, Music, Download, Youtube, Search } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Card, CardContent } from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Separator } from "$lib/components/ui/separator";
  import { fade, fly } from 'svelte/transition';
  
  let url: string = '';
  let isLoading = false;
  let isDownloading = false;
  let error = '';
  
  type PlaylistData = {
    title: string;
    channelName: string;
    videoCount: number;
    totalDuration: string;
    thumbnailUrl: string;
    songs: Array<{
      title: string;
      duration: string;
      thumbnail: string;
    }>;
  } | null;

  let playlistData: PlaylistData = null;

  const mockSongs = [
    { title: "Summer Nights - Extended Mix", duration: "5:23", thumbnail: "/api/placeholder/50/50" },
    { title: "Ocean Breeze (Original Mix)", duration: "4:17", thumbnail: "/api/placeholder/50/50" },
    { title: "Sunset Dreams", duration: "6:45", thumbnail: "/api/placeholder/50/50" }
  ];

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    isLoading = true;
    error = '';
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (url.includes('youtube.com/playlist')) {
      playlistData = {
        title: "Ultimate Summer Mix 2024",
        channelName: "Electronic Vibes",
        videoCount: 42,
        totalDuration: "3:15:00",
        thumbnailUrl: "/api/placeholder/400/225",
        songs: mockSongs
      };
    } else {
      error = 'Please enter a valid YouTube playlist URL';
      playlistData = null;
    }
    
    isLoading = false;
  }

  async function handleDownload(event: MouseEvent) {
    isDownloading = true;
    await new Promise(resolve => setTimeout(resolve, 2000));
    isDownloading = false;
  }
</script>

<div class="min-h-screen bg-gradient-to-br from-red-500/5 via-background to-background">
<div class="max-w-3xl mx-auto p-6 pt-12 space-y-8">
  <!-- Header -->
  <div in:fly={{ y: -20, duration: 700 }}>
    <div class="space-y-6 text-center">
      <div class="inline-flex p-3 rounded-full bg-red-500/10">
        <Youtube class="w-8 h-8 text-red-500" />
      </div>
      <div class="space-y-2">
        <h1 class="text-4xl font-bold tracking-tight font-heading">
          YouTube Playlist Downloader
        </h1>
        <p class="text-muted-foreground max-w-md mx-auto font-heading">
          Convert YouTube playlists to high-quality MP3s with just one click
        </p>
      </div>
    </div>
  </div>

  <!-- Search Form -->
  <div in:fly={{ y: 20, duration: 700, delay: 200 }}>
    <Card class="backdrop-blur-xl bg-card/40">
      <CardContent class="pt-6">
        <form on:submit={handleSubmit} class="relative">
          <div class="absolute left-3 top-1/2 -translate-y-1/2">
            <Search class="w-4 h-4 text-muted-foreground" />
          </div>
          
          <Input
            type="url"
            bind:value={url}
            placeholder="Paste YouTube playlist URL"
            class="pl-10 pr-32 h-12 bg-background/50"
            required
          />
          
          <div class="absolute right-2 top-1/2 -translate-y-1/2">
            <Button 
              type="submit" 
              disabled={isLoading}
              size="sm"
              variant="secondary"
            >
              {#if isLoading}
                <Loader2 class="w-4 h-4 mr-2 animate-spin" />
                Processing
              {:else}
                Analyze
              {/if}
            </Button>
          </div>
        </form>

        {#if error}
          <div class="mt-4 p-3 rounded-lg bg-destructive/15 text-destructive text-sm" 
               transition:fade>
            {error}
          </div>
        {/if}
      </CardContent>
    </Card>
  </div>

  <!-- Playlist Details -->
  {#if playlistData}
    <div in:fly={{ y: 20, duration: 700 }}>
      <div class="space-y-6">
        <Card class="overflow-hidden backdrop-blur-xl bg-card/40">
          <!-- Playlist Header -->
          <div class="relative h-[225px]">
            <img
              src={playlistData.thumbnailUrl}
              alt="Playlist thumbnail"
              class="w-full h-full object-cover"
            />
            <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent"></div>
            <div class="absolute bottom-0 left-0 right-0 p-6 space-y-3">
              <h2 class="text-2xl font-bold text-white font-heading">
                {playlistData.title}
              </h2>
              <div class="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" class="bg-white/10 hover:bg-white/20">
                  {playlistData.channelName}
                </Badge>
                <Badge variant="secondary" class="bg-white/10 hover:bg-white/20">
                  {playlistData.videoCount} tracks
                </Badge>
                <Badge variant="secondary" class="bg-white/10 hover:bg-white/20">
                  {playlistData.totalDuration}
                </Badge>
              </div>
            </div>
          </div>

          <!-- Song List -->
          <div>
            {#each playlistData.songs as song, i}
              <div>
                <div class="flex items-center gap-4 p-4 hover:bg-accent/50 transition-colors">
                  <div class="text-sm text-muted-foreground w-6 text-center">
                    {i + 1}
                  </div>
                  <div class="relative w-10 h-10 rounded overflow-hidden">
                    <img
                      src={song.thumbnail}
                      alt={song.title}
                      class="object-cover"
                    />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium truncate font-heading">
                      {song.title}
                    </div>
                  </div>
                  <div class="text-sm text-muted-foreground">
                    {song.duration}
                  </div>
                </div>
                {#if i < playlistData.songs.length - 1}
                  <Separator class="opacity-[0.15]" />
                {/if}
              </div>
            {/each}
          </div>
        </Card>

        <!-- Download Button -->
        <Button 
          disabled={isDownloading}
          class="w-full h-12 text-base"
          size="lg"
        >
          {#if isDownloading}
            <Loader2 class="w-5 h-5 mr-2 animate-spin" />
            Preparing download...
          {:else}
            <Download class="w-5 h-5 mr-2" />
            Download as MP3
          {/if}
        </Button>
      </div>
    </div>
  {/if}

  <!-- Footer -->
  <div class="text-center font-heading">
    <Badge variant="secondary" class="bg-accent/50">
      <Music class="w-4 h-4 mr-2" />
      320kbps MP3 • ID3 tags • Album artwork included
    </Badge>
  </div>
</div>
</div>